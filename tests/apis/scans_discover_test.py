"""Tests for scans discover API request."""

import json

from ostorlab.apis import request
from ostorlab.apis import scans_discover


def testScansDiscoverAPIRequest_whenCalled_queryContainsGetPendingScansQuery() -> None:
    """Test scans discover API request contains the correct query."""
    api_request = scans_discover.ScansDiscoverAPIRequest()

    assert api_request.query is not None
    assert "query GetPendingScans" in api_request.query
    assert "$progresses: [String]" in api_request.query
    assert "$oldLockedScans: Boolean" in api_request.query
    assert "$numberElements: Int" in api_request.query


def testScansDiscoverAPIRequest_whenCalled_dataContainsCorrectVariables() -> None:
    """Test scans discover API request data contains correct variables."""
    api_request = scans_discover.ScansDiscoverAPIRequest()

    data = api_request.data
    assert data is not None
    assert "query" in data
    assert "variables" in data
    variables = json.loads(data["variables"])
    assert variables["progresses"] == ["not_started", "locked"]
    assert variables["oldLockedScans"] is True
    assert variables["numberElements"] == 50


def testScansDiscoverAPIRequest_whenCalled_endpointIsScannerGraphql() -> None:
    """Test scans discover API request has the correct endpoint."""
    api_request = scans_discover.ScansDiscoverAPIRequest()

    assert api_request.endpoint == request.SCANNER_GRAPHQL_ENDPOINT
