"""Tests for scan reserve API request."""

import json

from ostorlab.apis import scan_reserve


def testScanReserveAPIRequest_whenScanIdProvided_queryContainsReserveScanMutation()-> None:
    """Test scan reserve API request contains the correct mutation."""
    api_request = scan_reserve.ScanReserveAPIRequest(scan_id=1)

    assert api_request.query is not None
    assert "mutation ReserveScan" in api_request.query
    assert "$scanId: Int!" in api_request.query


def testScanReserveAPIRequest_whenScanIdProvided_dataContainsCorrectVariables()-> None:
    """Test scan reserve API request data contains correct variables."""
    api_request = scan_reserve.ScanReserveAPIRequest(scan_id=42)

    data = api_request.data
    assert data is not None
    assert "query" in data
    assert "variables" in data
    variables = json.loads(data["variables"])
    assert variables["scanId"] == 42


def testScanReserveAPIRequest_whenCalled_endpointIsScannerGraphql()-> None:
    """Test scan reserve API request has the correct endpoint."""
    api_request = scan_reserve.ScanReserveAPIRequest(scan_id=1)

    assert api_request.endpoint == "https://scanner.ostorlab.co/orchestrator/graphql"
