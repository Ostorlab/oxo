"""Tests for scan update state API request."""

import json

from ostorlab.apis import scan_update_state


def testScanUpdateStateAPIRequest_whenMinimal_queryContainsUpdateScanStateMutation() -> (
    None
):
    """Test minimal query contains the correct mutation and no asset details."""
    api_request = scan_update_state.ScanUpdateStateAPIRequest(
        scan_id=1, progress="started"
    )

    assert api_request.query is not None
    assert "mutation UpdateScanState" in api_request.query
    assert "$scanId: Int!" in api_request.query
    assert "$progress: String!" in api_request.query
    assert "deviceId: null" in api_request.query
    assert "asset" not in api_request.query
    assert "agentGroup" not in api_request.query


def testScanUpdateStateAPIRequest_whenFullDetails_queryContainsAssetAndAgentGroup() -> (
    None
):
    """Test full details query includes asset and agentGroup fields."""
    api_request = scan_update_state.ScanUpdateStateAPIRequest(
        scan_id=1, progress="locked", full_details=True
    )

    assert api_request.query is not None
    assert "mutation UpdateScanState" in api_request.query
    assert "$scanId: Int!" in api_request.query
    assert "deviceId: null" not in api_request.query
    assert "asset" in api_request.query
    assert "agentGroup" in api_request.query
    assert "... on UrlAssetType" in api_request.query
    assert "... on AndroidApkAssetType" in api_request.query
    assert "... on IosIpaAssetType" in api_request.query


def testScanUpdateStateAPIRequest_whenScanIdAndProgressProvided_dataContainsCorrectVariables() -> (
    None
):
    """Test scan update state API request data contains correct variables."""
    api_request = scan_update_state.ScanUpdateStateAPIRequest(
        scan_id=42, progress="finished"
    )

    data = api_request.data
    assert data is not None
    assert "query" in data
    assert "variables" in data
    variables = json.loads(data["variables"])
    assert variables["scanId"] == 42
    assert variables["progress"] == "finished"


def testScanUpdateStateAPIRequest_whenFullDetails_dataContainsSameVariables() -> None:
    """Test full details mode produces the same data structure."""
    api_request = scan_update_state.ScanUpdateStateAPIRequest(
        scan_id=7, progress="locked", full_details=True
    )

    data = api_request.data
    assert data is not None
    assert "query" in data
    assert "variables" in data
    variables = json.loads(data["variables"])
    assert variables["scanId"] == 7
    assert variables["progress"] == "locked"
