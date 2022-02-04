"""Tests for scan stop command."""
from click.testing import CliRunner
from ostorlab.cli import rootcli
from ostorlab.apis import request as api_request
from ostorlab.apis.runners import authenticated_runner
from ostorlab.runtimes.local import runtime as local_runtime

from unittest import mock


def testOstorlabScanStopCLI_whenRuntimeIsRemoteAndScanIdIsValid_stopsScan(requests_mock):
    """Test ostorlab scan stop command with valid scan id.
    Should stop the scan with the given scan id.
    """

    scan_data = {
        'data': {
            'stopScan': {
                'scan': {
                    'id': '123456'
                }
            }
        }
    }

    runner = CliRunner()
    requests_mock.post(authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=scan_data, status_code=200)
    result = runner.invoke(
        rootcli.rootcli, ['scan',  '--runtime=remote', 'stop', '--scan-id=123456'])

    assert result.exception is None
    assert 'Scan stopped successfully' in result.output


def testOstorlabScanStopCLI_whenRuntimeIsRemoteAndScanIdIsInValid_stopsScan(requests_mock):
    """Test ostorlab scan stop command with invalid scan id.
    Should show error message.
    """

    scan_data = {
        'errors': [
            {
                'message': 'Scan matching query does not exist.'
            }
        ]
    }

    runner = CliRunner()
    requests_mock.post(authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=scan_data, status_code=200)
    result = runner.invoke(
        rootcli.rootcli, ['scan',  '--runtime=remote', 'stop', '--scan-id=123456'])

    assert result.exception is None
    assert 'Scan with id 123456 not found' in result.output

@mock.patch.object(local_runtime.LocalRuntime, 'stop')
def testOstorlabScanStopCLI_whenRuntimeIsLocal_callsStopMethodWithProvidedId(mock_scan_stop):
    """Test ostorlab scan stop command with a scan id.
    Should call stop method with provided scan id.
    """

    mock_scan_stop.return_value = None
    runner = CliRunner()

    runner.invoke(
        rootcli.rootcli, ['scan',  '--runtime=local', 'stop', '--scan-id=123456'])

    mock_scan_stop.assert_called_once_with(scan_id='123456')
