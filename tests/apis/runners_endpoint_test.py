"""Tests for the configurable endpoints of the API runners."""

from typing import Any

import pytest
import pytest_httpx
from pytest_mock import plugin

from ostorlab.apis import request
from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis.runners import login_runner
from ostorlab.apis.runners import public_runner
from ostorlab.apis.runners import runner as base_runner
from ostorlab.apis.runners import scanner_runner


class _TestRequest(request.APIRequest):
    @property
    def query(self) -> str | None:
        return "query { test }"

    @property
    def data(self) -> dict[str, Any] | None:
        return {"query": self.query}


@pytest.mark.parametrize(
    ("api_runner", "expected_endpoint"),
    [
        (
            authenticated_runner.AuthenticatedAPIRunner(api_key="key"),
            authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        ),
        (public_runner.PublicAPIRunner(), public_runner.PUBLIC_GRAPHQL_ENDPOINT),
        (login_runner.LoginAPIRunner(), login_runner.TOKEN_ENDPOINT),
        (
            scanner_runner.ScannerAPIRunner(api_key="key"),
            scanner_runner.SCANNER_GRAPHQL_ENDPOINT,
        ),
    ],
)
def testRunnerEndpoint_whenNoEndpointProvided_usesDefaultEndpoint(
    api_runner: base_runner.APIRunner, expected_endpoint: str
) -> None:
    """Runners fall back to the Ostorlab endpoints when none is configured."""
    assert api_runner.endpoint == expected_endpoint


def testAuthenticatedRunnerExecute_whenEndpointProvided_sendsRequestToEndpoint(
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """The authenticated runner posts to the configured API endpoint."""
    httpx_mock.add_response(
        method="POST",
        url="https://re.example.com/apis/graphql",
        json={"data": {"test": "ok"}},
    )
    api_runner = authenticated_runner.AuthenticatedAPIRunner(
        api_key="key", endpoint="https://re.example.com/apis/graphql"
    )

    response = api_runner.execute(_TestRequest())

    assert response == {"data": {"test": "ok"}}


def testScannerRunnerExecute_whenEndpointProvided_sendsRequestToEndpoint(
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """The scanner runner posts to the configured scanner endpoint."""
    httpx_mock.add_response(
        method="POST",
        url="https://se.example.com/orchestrator/graphql",
        json={"data": {"test": "ok"}},
    )
    api_runner = scanner_runner.ScannerAPIRunner(
        api_key="key", endpoint="https://se.example.com/orchestrator/graphql"
    )

    response = api_runner.execute(_TestRequest())

    assert response == {"data": {"test": "ok"}}


def testAuthenticatedRunnerAuthenticate_whenEndpointProvided_logsInOnSiblingTokenEndpoint(
    httpx_mock: pytest_httpx.HTTPXMock, mocker: plugin.MockerFixture
) -> None:
    """Login targets the token endpoint next to the configured API endpoint."""
    set_token_mock = mocker.patch(
        "ostorlab.configuration_manager.ConfigurationManager.set_authorization_token"
    )
    httpx_mock.add_response(
        method="POST",
        url="https://re.example.com/apis/token/",
        json={"token": "the-token"},
    )
    api_runner = authenticated_runner.AuthenticatedAPIRunner(
        username="user",
        password="password",
        endpoint="https://re.example.com/apis/graphql",
    )

    api_runner.authenticate()

    set_token_mock.assert_called_once_with(authorization_token="the-token")
