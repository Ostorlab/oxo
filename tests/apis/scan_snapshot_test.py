"""Tests for the scan snapshot API requests."""

import json

from ostorlab.apis import scan_snapshot


def testClearScanSnapshotAPIRequest_always_clearsTheSnapshotFlagOnly() -> None:
    api_request = scan_snapshot.ClearScanSnapshotAPIRequest(scan_id=42)

    assert api_request.query is not None
    assert "updateScan(scanId: $scanId, hasSnapshot: false)" in api_request.query
    assert "progress" not in api_request.query
    assert json.loads(api_request.data["variables"]) == {"scanId": 42}
