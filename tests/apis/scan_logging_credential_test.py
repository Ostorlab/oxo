"""Tests for the scan logging credential API request."""

import json

from ostorlab.apis import scan_logging_credential


def testScanLoggingCredentialAPIRequest_always_createsCorrectQuery() -> None:
    """Verify the query is correctly formed."""
    request = scan_logging_credential.ScanLoggingCredentialAPIRequest()

    assert "query ScanLoggingCredential" in request.query
    assert "scanLoggingCredential" in request.query

    data = request.data
    assert "query" in data
    assert "variables" in data
    assert json.loads(data["variables"]) == {}
