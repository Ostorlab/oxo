"""Tests for scanner API runner."""

from typing import Any
from unittest import mock

import httpx
import tenacity
from pytest_mock import plugin

from ostorlab.apis import request
from ostorlab.apis.runners import runner as api_runner
from ostorlab.apis.runners import scanner_runner


class _TestRequest(request.APIRequest):
    @property
    def query(self) -> str | None:
        return "query { test }"

    @property
    def data(self) -> dict[str, Any] | None:
        return {"query": self.query}


class _MutationRequest(request.APIRequest):
    @property
    def query(self) -> str | None:
        return "mutation { updateScan }"

    @property
    def data(self) -> dict[str, Any] | None:
        return {"query": self.query}


_NO_WAIT = tenacity.wait_fixed(0)


def _make_runner(
    retry_wait: tenacity.wait.WaitBaseT = _NO_WAIT,
) -> scanner_runner.ScannerAPIRunner:
    return scanner_runner.ScannerAPIRunner(api_key="test-key", retry_wait=retry_wait)


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
        except api_runner.ResponseError:
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
        except api_runner.ResponseError:
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


def testScannerAPIRunner_whenServerErrorThenSuccess_retriesAndReturnsData(
    mocker: plugin.MockerFixture,
) -> None:
    """Test execute retries a transient server error and returns data on the retry."""
    runner = _make_runner()
    req = _TestRequest()

    post_mock = mock.MagicMock(
        side_effect=[
            httpx.Response(502, content=b"Bad gateway"),
            httpx.Response(200, json={"data": {"test": "ok"}}),
        ]
    )
    with mock.patch.object(httpx, "Client", autospec=True) as mock_client:
        mock_client.return_value.__enter__.return_value.post = post_mock
        result = runner.execute(req)

    assert result == {"data": {"test": "ok"}}
    assert post_mock.call_count == 2


def testScannerAPIRunner_whenPersistentServerError_raisesResponseError() -> None:
    """Test execute raises ResponseError once the retry budget is exhausted."""
    runner = _make_runner()
    req = _TestRequest()

    post_mock = mock.MagicMock(return_value=httpx.Response(502, content=b"Bad gateway"))
    with mock.patch.object(httpx, "Client", autospec=True) as mock_client:
        mock_client.return_value.__enter__.return_value.post = post_mock
        try:
            runner.execute(req)
            assert False, "Expected ResponseError"
        except api_runner.ResponseError:
            pass

    assert post_mock.call_count == scanner_runner.SCANNER_REQUEST_ATTEMPTS


def testScannerAPIRunner_whenTransportErrorThenSuccess_retriesAndReturnsData(
    mocker: plugin.MockerFixture,
) -> None:
    """Test execute retries a transient transport error and returns data on the retry."""
    runner = _make_runner()
    req = _TestRequest()

    post_mock = mock.MagicMock(
        side_effect=[
            httpx.ConnectError("connection refused"),
            httpx.Response(200, json={"data": {"test": "ok"}}),
        ]
    )
    with mock.patch.object(httpx, "Client", autospec=True) as mock_client:
        mock_client.return_value.__enter__.return_value.post = post_mock
        result = runner.execute(req)

    assert result == {"data": {"test": "ok"}}
    assert post_mock.call_count == 2


def testScannerAPIRunner_whenConnectTimeoutThenSuccess_retriesAndReturnsData(
    mocker: plugin.MockerFixture,
) -> None:
    """Test execute retries a connect timeout and returns data on the retry."""
    runner = _make_runner()
    req = _TestRequest()

    post_mock = mock.MagicMock(
        side_effect=[
            httpx.ConnectTimeout("timed out"),
            httpx.Response(200, json={"data": {"test": "ok"}}),
        ]
    )
    with mock.patch.object(httpx, "Client", autospec=True) as mock_client:
        mock_client.return_value.__enter__.return_value.post = post_mock
        result = runner.execute(req)

    assert result == {"data": {"test": "ok"}}
    assert post_mock.call_count == 2


def testScannerAPIRunner_whenPersistentTransportError_raises() -> None:
    """Test execute raises the transport error once the retry budget is exhausted."""
    runner = _make_runner()
    req = _TestRequest()

    post_mock = mock.MagicMock(side_effect=httpx.ConnectError("connection refused"))
    with mock.patch.object(httpx, "Client", autospec=True) as mock_client:
        mock_client.return_value.__enter__.return_value.post = post_mock
        try:
            runner.execute(req)
            assert False, "Expected ConnectError"
        except httpx.ConnectError:
            pass

    assert post_mock.call_count == scanner_runner.SCANNER_REQUEST_ATTEMPTS


def testScannerAPIRunner_whenMutationReturnsServerError_doesNotRetry() -> None:
    """Test execute does not retry mutations, whatever the response status."""
    runner = _make_runner()
    req = _MutationRequest()

    post_mock = mock.MagicMock(return_value=httpx.Response(502, content=b"Bad gateway"))
    with mock.patch.object(httpx, "Client", autospec=True) as mock_client:
        mock_client.return_value.__enter__.return_value.post = post_mock
        try:
            runner.execute(req)
            assert False, "Expected ResponseError"
        except api_runner.ResponseError:
            pass

    assert post_mock.call_count == 1


def testScannerAPIRunner_whenMutationTransportError_doesNotRetry() -> None:
    """Test execute does not retry mutations, whatever the raised exception."""
    runner = _make_runner()
    req = _MutationRequest()

    post_mock = mock.MagicMock(side_effect=httpx.ConnectError("connection refused"))
    with mock.patch.object(httpx, "Client", autospec=True) as mock_client:
        mock_client.return_value.__enter__.return_value.post = post_mock
        try:
            runner.execute(req)
            assert False, "Expected ConnectError"
        except httpx.ConnectError:
            pass

    assert post_mock.call_count == 1
