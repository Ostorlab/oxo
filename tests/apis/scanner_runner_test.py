"""Tests for scanner API runner."""

from typing import Any
from unittest import mock

import httpx

from ostorlab.apis import request
from ostorlab.apis.runners import scanner_runner


class _TestRequest(request.APIRequest):
    @property
    def query(self) -> str | None:
        return "query { test }"

    @property
    def data(self) -> dict[str, Any] | None:
        return {"query": self.query}


def _make_runner() -> scanner_runner.ScannerAPIRunner:
    return scanner_runner.ScannerAPIRunner(
        api_key="test-key",
    )


def testScannerAPIRunner_whenExecuteSendsRequest_usesApiKeyHeader() -> None:
    """Test execute sends request with X-Api-Key header."""
    runner = _make_runner()
    req = _TestRequest()

    with mock.patch.object(httpx, "Client", autospec=True) as mock_client:
        mock_response = httpx.Response(200, json={"data": {"test": "ok"}})
        mock_client.return_value.__enter__.return_value.post.return_value = (
            mock_response
        )
        runner.execute(req)

    call_headers = mock_client.return_value.__enter__.return_value.post.call_args[1][
        "headers"
    ]
    assert call_headers["X-Api-Key"] == "test-key"


def testScannerAPIRunner_whenExecuteReturnsError_raisesResponseError() -> None:
    """Test execute raises ResponseError on non-200 status."""
    runner = _make_runner()
    req = _TestRequest()

    with mock.patch.object(httpx, "Client", autospec=True) as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = (
            httpx.Response(500, content=b"Internal error")
        )
        try:
            runner.execute(req)
            assert False, "Expected ResponseError"
        except scanner_runner.runner.ResponseError:
            pass


def testScannerAPIRunner_whenExecuteReturnsGraphQLError_raisesResponseError() -> None:
    """Test execute raises ResponseError on GraphQL errors."""
    runner = _make_runner()
    req = _TestRequest()

    with mock.patch.object(httpx, "Client", autospec=True) as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = (
            httpx.Response(200, json={"errors": [{"message": "Something went wrong"}]})
        )
        try:
            runner.execute(req)
            assert False, "Expected ResponseError"
        except scanner_runner.runner.ResponseError:
            pass


def testScannerAPIRunner_whenExecuteSucceeds_returnsData() -> None:
    """Test execute returns data on success."""
    runner = _make_runner()
    req = _TestRequest()

    with mock.patch.object(httpx, "Client", autospec=True) as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = (
            httpx.Response(200, json={"data": {"test": "ok"}})
        )
        result = runner.execute(req)

    assert result == {"data": {"test": "ok"}}


def testScannerAPIRunner_whenRequestIsJson_setsContentType() -> None:
    """Test _sent_request sets Content-Type to application/json."""
    runner = _make_runner()
    req = _TestRequest()

    with mock.patch.object(httpx, "Client", autospec=True) as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = (
            httpx.Response(200, json={"data": {"test": "ok"}})
        )
        runner._sent_request(req, headers={})

    call_headers = mock_client.return_value.__enter__.return_value.post.call_args[1][
        "headers"
    ]
    assert call_headers["Content-Type"] == "application/json"
