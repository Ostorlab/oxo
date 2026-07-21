"""Tests for scan update state API request."""

import json

from ostorlab.apis import scan_update_state


def testScanUpdateStateAPIRequest_whenScanIdAndProgressProvided_queryContainsUpdateScanStateMutation()-> None:
    """Test scan update state API request contains the correct mutation."""
    api_request = scan_update_state.ScanUpdateStateAPIRequest(
        scan_id=1, progress="started"
    )

    assert api_request.query is not None
    assert "mutation UpdateScanState" in api_request.query
    assert "$scanId: Int!" in api_request.query
    assert "$progress: String!" in api_request.query


def testScanUpdateStateAPIRequest_whenScanIdAndProgressProvided_dataContainsCorrectVariables()-> None:
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


def testScanUpdateStateAPIRequest_whenCalled_endpointIsScannerGraphql()-> None:
    """Test scan update state API request has the correct endpoint."""
    api_request = scan_update_state.ScanUpdateStateAPIRequest(
        scan_id=1, progress="started"
    )

    assert api_request.endpoint == "https://scanner.ostorlab.co/orchestrator/graphql"
