"""Tests for CLI agent search command."""

from click import testing
from ostorlab.apis.runners import public_runner, authenticated_runner

from ostorlab.cli import rootcli


def testAgentSearchCLI_WhenAuthenticatedRunner_listAgents(mocker, requests_mock):
    """Test ostorlab agent search CLI command with Autenticated API returns list of agents.
    """
    mocker.patch('ostorlab.configuration_manager.ConfigurationManager.is_authenticated', return_value=True)
    agents_dict = {'data': {'agents': [{'key': 'testKey', 'name': 'testName'}]}}
    requests_mock.post(authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
                       json=agents_dict, status_code=200)
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ['agent', 'search', '-k', 'xss'])

    assert 'Listing 1 Agents' in result.output
    assert 'testKey' in result.output
    assert 'testName' in result.output


def testAgentSearchCLI_WhenPublicRunner_listAgents(mocker, requests_mock):
    """Test ostorlab agent search CLI command with Public API returns list of agents.
    """
    mocker.patch('ostorlab.configuration_manager.ConfigurationManager.get_api_key_id', return_value=None)
    agents_dict = {'data': {'agents': [{'key': 'testKey', 'name': 'testName'}]}}
    requests_mock.post(public_runner.PUBLIC_GRAPHQL_ENDPOINT,
                       json=agents_dict, status_code=200)
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ['agent', 'search', '-k', 'xss'])

    assert 'Listing 1 Agents' in result.output
    assert 'testKey' in result.output
    assert 'testName' in result.output
