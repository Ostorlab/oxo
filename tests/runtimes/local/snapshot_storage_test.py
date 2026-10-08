"""Tests for the storage of scan snapshots in a bucket."""

import hashlib
import json

import pytest
from google.api_core import exceptions as gcloud_exceptions
from google.resumable_media import common as resumable_media_common
from pytest_mock import plugin

from ostorlab.runtimes.local import snapshot_storage

SERVICE_ACCOUNT_KEY = json.dumps({"type": "service_account"})


@pytest.fixture
def storage_client(mocker: plugin.MockerFixture):
    mocker.patch("google.oauth2.service_account.Credentials.from_service_account_info")
    return mocker.patch("google.cloud.storage.Client")


@pytest.mark.parametrize(
    "bucket_path, object_name",
    [
        ("gs://scan-snapshots/scan_snapshots", "scan_snapshots/42/snapshot.pb.gz"),
        ("gs://scan-snapshots/a/b/", "a/b/42/snapshot.pb.gz"),
        ("gs://scan-snapshots", "42/snapshot.pb.gz"),
        ("scan-snapshots/scan_snapshots", "scan_snapshots/42/snapshot.pb.gz"),
    ],
)
def testObjectName_always_isTheFixedPathOfTheScan(
    storage_client, bucket_path: str, object_name: str
) -> None:
    store = snapshot_storage.SnapshotStore(bucket_path, SERVICE_ACCOUNT_KEY)

    assert store.object_name(42) == object_name


@pytest.mark.parametrize(
    "bucket_path, service_account_key",
    [
        ("s3://scan-snapshots", SERVICE_ACCOUNT_KEY),
        ("gs://scan-snapshots", "not json"),
        ("gs://scan-snapshots", json.dumps("a string")),
    ],
)
def testSnapshotStore_whenSettingsAreInvalid_raisesSnapshotStorageError(
    storage_client, bucket_path: str, service_account_key: str
) -> None:
    with pytest.raises(snapshot_storage.SnapshotStorageError):
        snapshot_storage.SnapshotStore(bucket_path, service_account_key)


def testUpload_always_storesTheChecksumWithTheSnapshot(storage_client) -> None:
    blob = storage_client.return_value.__enter__.return_value.bucket.return_value.blob.return_value
    blob.generation = 7
    store = snapshot_storage.SnapshotStore(
        "gs://scan-snapshots/scan_snapshots", SERVICE_ACCOUNT_KEY
    )

    generation = store.upload(42, b"snapshot")

    assert generation == 7
    assert blob.metadata == {"sha256": hashlib.sha256(b"snapshot").hexdigest()}
    assert blob.upload_from_string.call_args.args[0] == b"snapshot"


def testDownload_whenObjectWasReplacedMeanwhile_fetchesTheVersionItChecked(
    storage_client,
) -> None:
    bucket = storage_client.return_value.__enter__.return_value.bucket.return_value
    blob = bucket.get_blob.return_value
    blob.generation = 7
    blob.metadata = {"sha256": hashlib.sha256(b"snapshot").hexdigest()}
    blob.download_as_bytes.return_value = b"snapshot"
    store = snapshot_storage.SnapshotStore("gs://scan-snapshots", SERVICE_ACCOUNT_KEY)

    stored = store.download(42)

    assert stored == snapshot_storage.StoredSnapshot(data=b"snapshot", generation=7)
    assert blob.download_as_bytes.call_args.kwargs["if_generation_match"] == 7


@pytest.mark.parametrize(
    "error",
    [gcloud_exceptions.NotFound("gone"), gcloud_exceptions.PreconditionFailed("new")],
)
def testDelete_whenObjectIsGoneOrReplaced_keepsQuiet(
    storage_client, error: Exception
) -> None:
    blob = storage_client.return_value.__enter__.return_value.bucket.return_value.blob.return_value
    blob.delete.side_effect = error
    store = snapshot_storage.SnapshotStore("gs://scan-snapshots", SERVICE_ACCOUNT_KEY)

    store.delete(42, generation=7)

    blob.delete.assert_called_once_with(if_generation_match=7)


def testDelete_whenStorageFails_raisesSnapshotStorageError(storage_client) -> None:
    blob = storage_client.return_value.__enter__.return_value.bucket.return_value.blob.return_value
    blob.delete.side_effect = gcloud_exceptions.ServiceUnavailable("try later")
    store = snapshot_storage.SnapshotStore("gs://scan-snapshots", SERVICE_ACCOUNT_KEY)

    with pytest.raises(snapshot_storage.SnapshotStorageError):
        store.delete(42, generation=7)


def testSnapshotStore_whenKeyMissesServiceAccountFields_raisesSnapshotStorageError() -> (
    None
):
    """A JSON object that is not a usable service account key is rejected with the storage error."""
    with pytest.raises(snapshot_storage.SnapshotStorageError):
        snapshot_storage.SnapshotStore(
            "gs://scan-snapshots", json.dumps({"type": "service_account"})
        )


def testDownload_whenTransferIsCorrupted_raisesRetryableStorageError(
    storage_client,
) -> None:
    bucket = storage_client.return_value.__enter__.return_value.bucket.return_value
    blob = bucket.get_blob.return_value
    blob.generation = 7
    blob.metadata = {"sha256": "0" * 64}
    blob.download_as_bytes.side_effect = resumable_media_common.DataCorruption(
        None, "crc32c mismatch"
    )
    store = snapshot_storage.SnapshotStore("gs://scan-snapshots", SERVICE_ACCOUNT_KEY)

    with pytest.raises(snapshot_storage.SnapshotStorageError):
        store.download(42)


def testUpload_whenTransferIsCorrupted_raisesRetryableStorageError(
    storage_client,
) -> None:
    blob = storage_client.return_value.__enter__.return_value.bucket.return_value.blob.return_value
    blob.upload_from_string.side_effect = resumable_media_common.DataCorruption(
        None, "crc32c mismatch"
    )
    store = snapshot_storage.SnapshotStore("gs://scan-snapshots", SERVICE_ACCOUNT_KEY)

    with pytest.raises(snapshot_storage.SnapshotStorageError):
        store.upload(42, b"snapshot")


@pytest.mark.parametrize(
    "missing",
    [
        {"return_value": None},
        {"side_effect": gcloud_exceptions.NotFound("gone")},
    ],
)
def testDownload_whenObjectIsMissing_raisesSnapshotNotFound(
    storage_client, missing: dict
) -> None:
    bucket = storage_client.return_value.__enter__.return_value.bucket.return_value
    bucket.get_blob.configure_mock(**missing)
    store = snapshot_storage.SnapshotStore("gs://scan-snapshots", SERVICE_ACCOUNT_KEY)

    with pytest.raises(snapshot_storage.SnapshotNotFoundError):
        store.download(42)


def testDownload_whenBytesDoNotMatchTheirChecksum_raisesSnapshotCorrupted(
    storage_client,
) -> None:
    blob = storage_client.return_value.__enter__.return_value.bucket.return_value.get_blob.return_value
    blob.generation = 7
    blob.metadata = {"sha256": hashlib.sha256(b"snapshot").hexdigest()}
    blob.download_as_bytes.return_value = b"tampered"
    store = snapshot_storage.SnapshotStore("gs://scan-snapshots", SERVICE_ACCOUNT_KEY)

    with pytest.raises(snapshot_storage.SnapshotCorruptedError):
        store.download(42)
