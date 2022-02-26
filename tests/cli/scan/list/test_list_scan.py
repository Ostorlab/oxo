"""Tests for scan list command."""

from click.testing import CliRunner
from unittest import mock

from ostorlab.cli import rootcli
from ostorlab.cli import console
from ostorlab.apis.runners import authenticated_runner
from ostorlab.runtimes.local import runtime as local_runtime
from ostorlab.runtimes import runtime


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
    requests_mock.post(authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=scans_data, status_code=200)
    result = runner.invoke(rootcli.rootcli, ['scan',  '--runtime=remote', 'list'])

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
    requests_mock.post(authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=None, status_code=401)
    result = runner.invoke(rootcli.rootcli, ['scan', '--runtime=remote', 'list'])
    assert result.exception is None
    mock_console.assert_called()


@mock.patch.object(local_runtime.LocalRuntime, 'list')
def testOstorlabScanListCLI_whenRuntimeIsLocal_showsListOfScans(mock_scan_list, mocker):
    """Test ostorlab scan list command with local as the runtime option.
    Should show list of scans.
    """

    services = [{
        'CreatedAt': '2021-12-27T13:37:02.795789947Z',
        'Spec': {'Labels': {'ostorlab.universe': 'qmwjef'}}},
        {
            'CreatedAt': '2021-12-27T13:37:02.095789947Z',
            'Spec': {'Labels': {'ostorlab.universe': 'klwjfh'}}}
    ]
    scans = [runtime.Scan(
        id=service['Spec']['Labels']['ostorlab.universe'],
        asset='File(/tmp/test)',
        created_time=service['CreatedAt'],
        progress=None,
    ) for service in services]

    mock_scan_list.return_value = scans
    mocker.patch('ostorlab.runtimes.local.LocalRuntime.__init__', return_value=None)
    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli, ['scan',  '--runtime=local', 'list'])

    assert all(scan.id in result.output for scan in scans)
    mock_scan_list.assert_called()
