"""Storage of scan snapshots in a Google Cloud Storage bucket.

The snapshot of a scan is stored at a fixed path, `<bucket path>/<scan id>/snapshot.pb.gz`, so the stop scan agent
uploading it and the scanner restoring it find it from the scan id alone. A new pause of the scan overwrites it. The
sha256 of the snapshot is kept in the object metadata and checked when the snapshot is downloaded.

The bucket path and the service account key are scanner settings (`oxo scanner --snapshot-bucket
--snapshot-service-account`), the scanner passes them to the stop scan agent of each scan.

The module only depends on google-cloud-storage when a snapshot is stored or fetched.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from urllib import parse

from ostorlab import exceptions

try:
    from google.api_core import exceptions as gcloud_exceptions
    from google.auth import exceptions as auth_exceptions
    from google.cloud import storage
    from google.oauth2 import service_account
    from google.resumable_media import common as resumable_media_common
except ImportError:
    gcloud_exceptions = None
    auth_exceptions = None
    storage = None
    service_account = None
    resumable_media_common = None

SNAPSHOT_OBJECT_NAME = "snapshot.pb.gz"
SHA256_METADATA_KEY = "sha256"
# Environment variables passing the snapshot storage settings from the scanner to the stop scan agent.
BUCKET_ENV = "OSTORLAB_SNAPSHOT_BUCKET"
SERVICE_ACCOUNT_ENV = "OSTORLAB_SNAPSHOT_SERVICE_ACCOUNT"


class Error(exceptions.OstorlabError):
    """Base error of the snapshot storage."""


class SnapshotStorageError(Error):
    """The storage is not configured or unreachable, the request can be retried."""


class SnapshotNotFoundError(Error):
    """The snapshot object does not exist, it will not appear on a retry."""


class SnapshotCorruptedError(Error):
    """The snapshot object does not match its checksum, it will not be fixed on a retry."""


@dataclasses.dataclass(frozen=True)
class StoredSnapshot:
    """A snapshot object, identified by its generation so a newer upload is never deleted in its place."""

    data: bytes
    generation: int


@dataclasses.dataclass(frozen=True)
class SnapshotStorageSettings:
    """Snapshot storage settings of a scanner, passed down to its scans and to their stop scan agent."""

    bucket_path: str
    # Kept out of the representation: the settings may be logged or appear in an error.
    service_account_key: str = dataclasses.field(repr=False)

    def store(self) -> SnapshotStore:
        return SnapshotStore(self.bucket_path, self.service_account_key)


class SnapshotStore:
    """Upload, download and delete the snapshots of scans in a bucket."""

    def __init__(self, bucket_path: str, service_account_key: str) -> None:
        """
        Args:
            bucket_path: Bucket and optional prefix, like `gs://scan-snapshots/scan_snapshots`.
            service_account_key: JSON key of a service account allowed to read, write and delete objects there.

        Raises:
            SnapshotStorageError: When the settings are invalid or google-cloud-storage is not installed.
        """
        if storage is None:
            raise SnapshotStorageError(
                "storing scan snapshots requires the google-cloud-storage package."
            )
        self._bucket_name, self._prefix = _parse_bucket_path(bucket_path)
        self._credentials = _load_credentials(service_account_key)

    def object_name(self, scan_id: int) -> str:
        """Name of the snapshot object of a scan in the bucket."""
        return "/".join(
            part
            for part in (self._prefix, str(scan_id), SNAPSHOT_OBJECT_NAME)
            if part != ""
        )

    def upload(self, scan_id: int, data: bytes) -> int:
        """Store the snapshot of a scan, replacing the previous one.

        Returns:
            The generation of the uploaded object.

        Raises:
            SnapshotStorageError: When the upload fails.
        """
        try:
            with self._client() as client:
                blob = client.bucket(self._bucket_name).blob(self.object_name(scan_id))
                blob.metadata = {SHA256_METADATA_KEY: hashlib.sha256(data).hexdigest()}
                blob.upload_from_string(data, content_type="application/gzip")
                return int(blob.generation)
        except (
            gcloud_exceptions.GoogleAPIError,
            auth_exceptions.GoogleAuthError,
            # The checksum of the transfer did not match, the library removes the corrupted object.
            resumable_media_common.DataCorruption,
        ) as e:
            raise SnapshotStorageError(
                f"could not upload the snapshot of scan {scan_id}: {e}"
            ) from e

    def download(self, scan_id: int) -> StoredSnapshot:
        """Fetch the snapshot of a scan and check its checksum.

        Raises:
            SnapshotNotFoundError: When the scan has no snapshot object.
            SnapshotCorruptedError: When the snapshot does not match its sha256.
            SnapshotStorageError: When the download fails or the bucket does not exist.
        """
        try:
            with self._client() as client:
                blob = client.bucket(self._bucket_name).get_blob(
                    self.object_name(scan_id)
                )
                if blob is None:
                    # A missing bucket also reads as a missing object: a mistyped bucket must not make every
                    # paused scan start over.
                    self._check_bucket_exists(client)
                    raise SnapshotNotFoundError(
                        f"snapshot of scan {scan_id} not found."
                    )
                data = _download_blob(blob, scan_id)
        except gcloud_exceptions.NotFound as e:
            raise SnapshotNotFoundError(f"snapshot of scan {scan_id} not found.") from e
        except (
            gcloud_exceptions.GoogleAPIError,
            auth_exceptions.GoogleAuthError,
            resumable_media_common.DataCorruption,
        ) as e:
            raise SnapshotStorageError(
                f"could not download the snapshot of scan {scan_id}: {e}"
            ) from e
        if blob.metadata is None or SHA256_METADATA_KEY not in blob.metadata:
            raise SnapshotCorruptedError(
                f"snapshot of scan {scan_id} has no {SHA256_METADATA_KEY} metadata."
            )
        if blob.metadata[SHA256_METADATA_KEY] != hashlib.sha256(data).hexdigest():
            raise SnapshotCorruptedError(
                f"snapshot of scan {scan_id} does not match its checksum."
            )
        return StoredSnapshot(data=data, generation=int(blob.generation))

    def delete(self, scan_id: int, generation: int) -> None:
        """Delete the snapshot of a scan if it is still the given generation, a newer snapshot is kept.

        Raises:
            SnapshotStorageError: When the deletion fails for another reason than the object being gone or replaced.
        """
        try:
            with self._client() as client:
                client.bucket(self._bucket_name).blob(self.object_name(scan_id)).delete(
                    if_generation_match=generation
                )
        except (gcloud_exceptions.NotFound, gcloud_exceptions.PreconditionFailed):
            # Already deleted, or replaced by the snapshot of a later pause.
            return
        except (gcloud_exceptions.GoogleAPIError, auth_exceptions.GoogleAuthError) as e:
            raise SnapshotStorageError(
                f"could not delete the snapshot of scan {scan_id}: {e}"
            ) from e

    def _check_bucket_exists(self, client: storage.Client) -> None:
        """Raise when the bucket does not exist.

        Listing objects only needs object permissions, unlike reading the bucket, and fails with `NotFound` on a
        missing bucket.

        Raises:
            SnapshotStorageError: When the bucket does not exist.
        """
        try:
            next(iter(client.list_blobs(self._bucket_name, max_results=1)), None)
        except gcloud_exceptions.NotFound as e:
            raise SnapshotStorageError(
                f"snapshot bucket {self._bucket_name} does not exist."
            ) from e

    def _client(self) -> storage.Client:
        # The project is taken from the key: without it the client looks it up in the environment and raises an
        # `OSError` when it is not found. A key without project still works, bucket requests do not need one.
        return storage.Client(
            credentials=self._credentials, project=self._credentials.project_id
        )


def _download_blob(blob: storage.Blob, scan_id: int) -> bytes:
    """Download the generation of the blob that was read, so the bytes always match the metadata read with it.

    Raises:
        SnapshotStorageError: When the object was replaced or deleted since it was read, a retry reads it again.
    """
    try:
        try:
            return blob.download_as_bytes(
                if_generation_match=blob.generation, checksum="crc32c"
            )
        except resumable_media_common.DataCorruption:
            # A damaged transfer or an object corrupted for good: downloaded again without the crc32c check, the
            # sha256 tells them apart.
            return blob.download_as_bytes(
                if_generation_match=blob.generation, checksum=None
            )
    except gcloud_exceptions.NotFound as e:
        # The download fetches the generation read, a bucket without versioning drops it once the object is
        # replaced. The snapshot is not lost, a retry fetches the new one.
        raise SnapshotStorageError(
            f"snapshot of scan {scan_id} changed during its download: {e}"
        ) from e


def _parse_bucket_path(bucket_path: str) -> tuple[str, str]:
    try:
        parsed = parse.urlparse(
            bucket_path if "://" in bucket_path else f"gs://{bucket_path}"
        )
    except ValueError as e:
        raise SnapshotStorageError(
            f"snapshot bucket must look like gs://<bucket>[/<prefix>], got {bucket_path!r}."
        ) from e
    if parsed.scheme != "gs" or parsed.netloc == "":
        raise SnapshotStorageError(
            f"snapshot bucket must look like gs://<bucket>[/<prefix>], got {bucket_path!r}."
        )
    return parsed.netloc, parsed.path.strip("/")


def _load_credentials(service_account_key: str) -> service_account.Credentials:
    try:
        key_info = json.loads(service_account_key)
    except json.JSONDecodeError as e:
        raise SnapshotStorageError(
            "snapshot service account key is not valid JSON."
        ) from e
    if isinstance(key_info, dict) is False:
        raise SnapshotStorageError(
            "snapshot service account key is not a service account key."
        )
    try:
        return service_account.Credentials.from_service_account_info(key_info)
    # A key missing a field raises google.auth `MalformedError`, a `ValueError`.
    except (ValueError, TypeError) as e:
        raise SnapshotStorageError(
            "snapshot service account key is not a service account key."
        ) from e
