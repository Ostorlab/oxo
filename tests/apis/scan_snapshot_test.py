"""Tests for the scan snapshot API requests."""

import json

from ostorlab.apis import scan_snapshot


def testScanSnapshotAPIRequest_always_queriesTheSignedDownloadUrlOfTheScanSnapshot() -> (
    None
):
    api_request = scan_snapshot.ScanSnapshotAPIRequest(scan_id=42)

    assert api_request.query is not None
    assert "scanSnapshot(scanId: $scanId)" in api_request.query
    for field in ("size", "sha256", "downloadUrl"):
        assert field in api_request.query
    assert json.loads(api_request.data["variables"]) == {"scanId": 42}


def testDeleteScanSnapshotAPIRequest_always_sendsTheChecksumAsRequired() -> None:
    api_request = scan_snapshot.DeleteScanSnapshotAPIRequest(
        scan_id=42, sha256="a" * 64
    )

    assert api_request.query is not None
    assert "$sha256: String!" in api_request.query
    assert "deleteScanSnapshot(scanId: $scanId, sha256: $sha256)" in api_request.query
    assert json.loads(api_request.data["variables"]) == {
        "scanId": 42,
        "sha256": "a" * 64,
    }
