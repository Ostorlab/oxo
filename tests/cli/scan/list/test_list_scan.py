"""Tests for scan list command."""

import docker
import pytest

from click.testing import CliRunner
from ostorlab.cli import rootcli
from ostorlab.cli import console
from ostorlab.apis import request as api_request
from ostorlab.runtimes.local import runtime as local_runtime

from unittest import mock


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
    requests_mock.post(api_request.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=None, status_code=401)
    result = runner.invoke(rootcli.rootcli, ['scan', '--runtime=remote', 'list'])
    assert result.exception is None
    mock_console.assert_called()


@pytest.mark.docker
def testOstorlabScanListCLI_whenRuntimeOptionIsLocal_showsScansInfo():
    """Test ostorlab scan list command with local as the runtime option.
    Should show scans information.
    """

    local_runtime_instance = local_runtime.LocalRuntime()
    runner = CliRunner()
    docker_client = docker.from_env()
    services = docker_client.services.list(
        filters={'label': 'ostorlab.universe'})
    scans = local_runtime_instance.list()
    result = runner.invoke(rootcli.rootcli, ['scan',  '--runtime=local', 'list'])

    assert isinstance(scans, list) is True
    assert any(scan.id in result.output for scan in scans)
    assert any(s.attrs['Spec']['Labels'].get('ostorlab.universe') in result.output for s in services)
