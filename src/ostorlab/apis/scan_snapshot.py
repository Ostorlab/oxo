"""Fetch and delete the snapshot a paused scan resumes from."""

import json
from typing import Any

from ostorlab.apis import request


class ScanSnapshotAPIRequest(request.APIRequest):
    """Fetch the snapshot metadata of a paused scan, with a short-lived signed URL to download its bytes."""

    def __init__(self, scan_id: int) -> None:
        self._scan_id = scan_id

    @property
    def query(self) -> str | None:
        return """
        query ScanSnapshot($scanId: Int!) {
          scanSnapshot(scanId: $scanId) {
            scanId
            size
            sha256
            downloadUrl
          }
        }
        """

    @property
    def data(self) -> dict[str, Any] | None:
        return {
            "query": self.query,
            "variables": json.dumps({"scanId": self._scan_id}),
        }


class DeleteScanSnapshotAPIRequest(request.APIRequest):
    """Delete the snapshot of a scan once it was restored.

    Only the snapshot matching the checksum of the restored one is deleted, a newer snapshot saved by a later pause of
    the scan is kept.
    """

    def __init__(self, scan_id: int, sha256: str) -> None:
        self._scan_id = scan_id
        self._sha256 = sha256

    @property
    def query(self) -> str | None:
        return """
        mutation DeleteScanSnapshot($scanId: Int!, $sha256: String!) {
          deleteScanSnapshot(scanId: $scanId, sha256: $sha256) {
            deleted
          }
        }
        """

    @property
    def data(self) -> dict[str, Any] | None:
        return {
            "query": self.query,
            "variables": json.dumps({"scanId": self._scan_id, "sha256": self._sha256}),
        }
