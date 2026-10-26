"""Unit Tests for auth revoke command."""

from unittest import mock

import pytest_httpx
from click.testing import CliRunner

from ostorlab import configuration_manager
from ostorlab.apis.runners import authenticated_runner
from ostorlab.cli import rootcli


def testOstorlabAuthRevokeCLI_whenValidApiKeyIdIsProvided_apiDataDeleted(
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """Test ostorlab auth revoke command with valid api key id.
    Should delete api data from storage.
    """

    api_data_dict = {"data": {"revokeApiKey": {"result": True}}}
    runner = CliRunner()
    httpx_mock.add_response(
        method="POST",
        url=authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=api_data_dict,
        status_code=200,
    )
    result = runner.invoke(rootcli.rootcli, ["auth", "revoke"])

    assert result.exception is None
    assert configuration_manager.ConfigurationManager().api_key is None


@mock.patch.object(
    configuration_manager.ConfigurationManager,
    "authorization_token",
    new_callable=mock.PropertyMock,
)
@mock.patch.object(authenticated_runner.AuthenticatedAPIRunner, "unauthenticate")
def testOstorlabAuthRevokeCLI_whenInvalidAuthorizationTokenProvided_logsError(
    mock_console: mock.MagicMock, httpx_mock: pytest_httpx.HTTPXMock
) -> None:
    """Test ostorlab auth logout command with wrong authorization token.
    Should unauthenticate user.
    """

    errors_dict = {"detail": "Invalid token."}

    mock_console.return_value = None
    runner = CliRunner()
    httpx_mock.add_response(
        method="POST",
        url=authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=errors_dict,
        status_code=401,
    )
    result = runner.invoke(rootcli.rootcli, ["auth", "revoke"])
    assert result.exception is None
    assert (
        "Error response. The reason could be the authorization token is invalid."
        in result.output.replace("\n", "")
    )


@mock.patch.object(
    configuration_manager.ConfigurationManager,
    "authorization_token",
    new_callable=mock.PropertyMock,
    return_value="expired-token",
)
@mock.patch.object(
    configuration_manager.ConfigurationManager, "delete_authorization_token_data"
)
def testOstorlabAuthRevokeCLI_whenServerRejectsAuthorizationToken_deletesLocalToken(
    mock_delete_authorization_token_data: mock.MagicMock,
    mock_authorization_token: mock.PropertyMock,
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """Test ostorlab auth revoke command when the server rejects the stored authorization token.
    Should still delete the local authorization token so the user is logged out.
    """
    runner = CliRunner()
    httpx_mock.add_response(
        method="POST",
        url=authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json={"detail": "Invalid token."},
        status_code=401,
    )

    result = runner.invoke(rootcli.rootcli, ["auth", "revoke"])

    assert result.exception is None
    mock_delete_authorization_token_data.assert_called_once_with()
