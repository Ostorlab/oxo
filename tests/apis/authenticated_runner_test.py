"""Authenticated HTTP request paths distinguish empty and populated errors."""

import pytest
import pytest_httpx

from ostorlab.apis import scan_create
from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis.runners import runner


@pytest.mark.parametrize("encoding", ["json", "ubjson"])
def testAuthenticatedRunner_whenErrorsEmpty_returnsSuccessfulHttpResponse(
    encoding: str, httpx_mock: pytest_httpx.HTTPXMock
) -> None:
    """Both request encodings accept a successful response with empty errors."""
    payload = {"data": {"createUiPrompts": {"uiPrompts": []}}, "errors": []}
    httpx_mock.add_response(json=payload)
    api_runner = authenticated_runner.AuthenticatedAPIRunner(api_key="test")
    request = scan_create.CreateUIPromptsAPIRequest([])

    response = (
        api_runner.execute(request)
        if encoding == "json"
        else api_runner.execute_ubjson_request(request)
    )

    assert response == payload
    sent_request = httpx_mock.get_request()
    assert sent_request is not None
    assert sent_request.headers["X-Api-Key"] == "test"
    assert sent_request.headers["Content-Type"] == (
        "application/json" if encoding == "json" else "application/ubjson"
    )


@pytest.mark.parametrize("encoding", ["json", "ubjson"])
def testAuthenticatedRunner_whenErrorsPopulated_raisesUsefulResponseError(
    encoding: str, httpx_mock: pytest_httpx.HTTPXMock
) -> None:
    """GraphQL error messages survive both real HTTP request paths."""
    httpx_mock.add_response(json={"errors": [{"message": "Access denied"}]})
    api_runner = authenticated_runner.AuthenticatedAPIRunner(api_key="test")
    request = scan_create.CreateUIPromptsAPIRequest([])

    with pytest.raises(runner.ResponseError, match="Response errors: Access denied"):
        if encoding == "json":
            api_runner.execute(request)
        else:
            api_runner.execute_ubjson_request(request)
