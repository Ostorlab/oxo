"""Tests for authenticated API runner."""

from typing import Any
from unittest import mock

import httpx

from ostorlab.apis import request
from ostorlab.apis.runners import authenticated_runner


class _RequestWithEndpoint(request.APIRequest):
    @property
    def query(self) -> str | None:
        return "query { test }"

    @property
    def data(self) -> dict[str, Any] | None:
        return {"query": self.query}

    @property
    def endpoint(self) -> str:
        return "https://custom.endpoint/graphql"


class _RequestWithoutEndpoint(request.APIRequest):
    @property
    def query(self) -> str | None:
        return "query { test }"

    @property
    def data(self) -> dict[str, Any] | None:
        return {"query": self.query}


def _make_runner() -> authenticated_runner.AuthenticatedAPIRunner:
    runner = authenticated_runner.AuthenticatedAPIRunner(
        username="test@test.com", password="test", api_key="test-key"
    )
    runner.unauthenticate()
    return runner


def testSentRequest_whenRequestHasCustomEndpoint_usesRequestEndpoint()-> None:
    """Test _sent_request uses request endpoint when request has custom endpoint."""
    runner = _make_runner()
    request_with_endpoint = _RequestWithEndpoint()

    with mock.patch.object(httpx, "Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = (
            httpx.Response(200, json={"data": {"test": "ok"}})
        )
        runner._sent_request(request_with_endpoint, headers={})

    call_url = mock_client.return_value.__enter__.return_value.post.call_args[0][0]
    assert call_url == "https://custom.endpoint/graphql"


def testSentRequest_whenRequestHasNoEndpoint_usesRunnerEndpoint()-> None:
    """Test _sent_request uses runner endpoint when request has no custom endpoint."""
    runner = _make_runner()
    request_without_endpoint = _RequestWithoutEndpoint()

    with mock.patch.object(httpx, "Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = (
            httpx.Response(200, json={"data": {"test": "ok"}})
        )
        runner._sent_request(request_without_endpoint, headers={})

    call_url = mock_client.return_value.__enter__.return_value.post.call_args[0][0]
    assert call_url == authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT


def testSendUbjsonRequest_whenRequestHasCustomEndpoint_usesRequestEndpoint()-> None:
    """Test _send_ubjson_request uses request endpoint when request has custom endpoint."""
    runner = _make_runner()
    request_with_endpoint = _RequestWithEndpoint()

    with mock.patch.object(httpx, "Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = (
            httpx.Response(200, json={"data": {"test": "ok"}})
        )
        runner._send_ubjson_request(request_with_endpoint, headers={})

    call_url = mock_client.return_value.__enter__.return_value.post.call_args[0][0]
    assert call_url == "https://custom.endpoint/graphql"


def testSendUbjsonRequest_whenRequestHasNoEndpoint_usesRunnerEndpoint()-> None:
    """Test _send_ubjson_request uses runner endpoint when request has no custom endpoint."""
    runner = _make_runner()
    request_without_endpoint = _RequestWithoutEndpoint()

    with mock.patch.object(httpx, "Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = (
            httpx.Response(200, json={"data": {"test": "ok"}})
        )
        runner._send_ubjson_request(request_without_endpoint, headers={})

    call_url = mock_client.return_value.__enter__.return_value.post.call_args[0][0]
    assert call_url == authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT
