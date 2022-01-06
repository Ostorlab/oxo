"""Tests for scan list command."""
from click.testing import CliRunner
from ostorlab.cli import rootcli
from ostorlab.cli import console
from ostorlab.apis import request as api_request

from unittest import mock


def testOstorlabScanListCLI_whenNoOptionsProvided_showsUsage():
    """Test ostorlab scan list command with no options and no sub command.
    Should show usage.
    """

    runner = CliRunner()

    result = runner.invoke(rootcli.rootcli, ['scan', 'list'])

    assert 'Usage: rootcli scan list [OPTIONS]\n' in result.output


def testOstorlabScanListCLI_whenCorrectCommandsAndOptionsProvided_showsScanInfo(requests_mock):
    """Test ostorlab scan list command with correct commands and options.
    Should show scans information.
    """

    scans_data = {
        'data': {
            'scans': {
                'pageInfo': {},
                'scans': []
            }
        }
    }

    runner = CliRunner()
    requests_mock.post(api_request.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=scans_data, status_code=200)
    result = runner.invoke(rootcli.rootcli, ['scan', 'list', '--source=remote'])

    assert result.exception is None

@mock.patch.object(console.Console, 'error')
def testOstorlabScanListCLI_whenUserIsNotAuthenticated_logsError(
        mock_console, requests_mock):
    """Test ostorlab scan list command with correct commands and options
    but the user is not authenticated.
    Should log an error.
    """

    mock_console.return_value = None
    runner = CliRunner()
    requests_mock.post(api_request.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=None, status_code=401)
    result = runner.invoke(rootcli.rootcli, ['scan', 'list', '--source=remote'])
    assert result.exception is None
    mock_console.assert_called()
