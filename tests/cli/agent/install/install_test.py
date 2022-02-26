"""Unittests for the CLI agent install command."""

import re

from click import testing
from docker.models import images as images_model

from ostorlab.apis.runners import public_runner
from ostorlab.cli import rootcli


def testAgentInstallCLI_whenRequiredOptionAgentKeyIsMissing_showMessage():
    """Test ostorlab agent install CLI command without the required agent_key option.
    Should show help message, and confirm the --agent option is missing.
    """
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ['agent', 'install'])

    assert 'Usage: rootcli agent install [OPTIONS]' in result.output
    assert 'Try \'rootcli agent install --help\' for help.' in result.output
    assert 'Error: Missing argument' in result.output


def testAgentInstallCLI_whenAgentDoesNotExist_commandExitsWithError(requests_mock):
    """Test ostorlab agent install CLI command with a wrong agent_key value.
    Should show message.
    """
    matcher = re.compile(r'http\+docker://(.*)/version')
    requests_mock.get(matcher, json={'ApiVersion': '1.42'}, status_code=200)

    api_call_response = {
        'errors': {'message': 'some error message.'}
    }
    requests_mock.post(public_runner.PUBLIC_GRAPHQL_ENDPOINT,
                        json=api_call_response, status_code=200)

    runner = testing.CliRunner()
    result = runner.invoke(rootcli.rootcli, ['agent', 'install', 'agent/wrong/key'])

    assert 'ERROR:' in result.output
    assert 'Please make sure you have the correct agent key.' in result.output
    assert result.exit_code == 2


def testAgentInstallCLI_whenAgentExists_installsAgent(mocker, requests_mock):
    """Test ostorlab agent install CLI command with a valid agent_key value should install the agent."""

    image_pull_mock = mocker.patch('docker.api.client.APIClient.pull', reutrn_value='dummy_log')
    image_get_mock = mocker.patch('docker.models.images.ImageCollection.get', return_value=images_model.Image())
    tag_image_mock = mocker.patch('docker.models.images.Image.tag', return_value=True)
    mocker.patch('ostorlab.cli.install_agent._is_image_present', return_value=False)

    api_call_response = {
        'data': {
            'agent': {
                'name': 'bigFuzzer',
                'gitLocation': '',
                'yamlFileLocation': '',
                'dockerLocation': 'ostorlab.store/library/busybox',
                'key': 'agent/OS/some_agentd',
                'versions': {
                    'versions': [
                        {
                            'version': '1.0.0'
                        }
                    ]
                }
            }
        }
    }
    requests_mock.post(public_runner.PUBLIC_GRAPHQL_ENDPOINT,
                       json=api_call_response, status_code=200)

    # The use of the following request mock is due to the fact that requests_mock fixture
    # requires mocking all requests. The docker api also sends some requests,
    # thus the following lines.
    matcher = re.compile(r'http\+docker://(.*)/version')
    requests_mock.get(matcher, json={'ApiVersion': '1.42'}, status_code=200)
    matcher = re.compile(r'http\+docker://(.*)/json')
    requests_mock.get(matcher, json={}, status_code=200)
    mocker.patch('ostorlab.runtimes.local.LocalRuntime.__init__', return_value=None)
    mocker.patch('ostorlab.cli.docker_requirements_checker.is_docker_working', return_value=True)
    runner = testing.CliRunner()
    result = runner.invoke(rootcli.rootcli, ['agent', 'install', 'agent/OT1/bigFuzzer'])
    image_pull_mock.assert_called()
    image_get_mock.assert_called()
    tag_image_mock.assert_called()
    assert 'Installation successful' in result.output
