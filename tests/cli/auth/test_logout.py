"""Unit Tests for auth logout command."""

from unittest import mock

import pytest_httpx
from click.testing import CliRunner

from ostorlab import configuration_manager
from ostorlab.cli import rootcli


@mock.patch.object(
    configuration_manager.ConfigurationManager, "delete_authorization_token_data"
)
def testOstorlabAuthLogoutCLI_always_deletesLocalAuthorizationToken(
    mock_delete_authorization_token_data: mock.MagicMock,
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """Test ostorlab auth logout command.
    Should delete the local authorization token without calling the API.
    """
    runner = CliRunner()

    result = runner.invoke(rootcli.rootcli, ["auth", "logout"])

    assert result.exception is None
    mock_delete_authorization_token_data.assert_called_once_with()
    assert "You successfully logged out" in result.output
