"""Tests for scan list API request."""

from ostorlab.apis import scan_list


def testScansListAPIRequest_whenNoStateIsProvided_generatesCorrectQuery():
    """Test scan list API request without state filter."""
    api_request = scan_list.ScansListAPIRequest(page=1, elements=10)

    assert api_request.query is not None
    assert "state" in api_request.query
    assert api_request.data is not None
    assert '"state"' not in api_request.data["variables"]


def testScansListAPIRequest_whenStateIsProvided_generatesCorrectQuery():
    """Test scan list API request with state filter."""
    api_request = scan_list.ScansListAPIRequest(page=1, elements=10, state="done")

    assert api_request.query is not None
    assert "state" in api_request.query
    assert api_request.data is not None
    assert '"state": "done"' in api_request.data["variables"]
