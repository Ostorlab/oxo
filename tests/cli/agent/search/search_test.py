"""Tests for CLI agent search command."""
from unittest import mock
from click import testing
from ostorlab.apis.runners import public_runner
from ostorlab.apis.runners import authenticated_runner

from ostorlab.cli import rootcli


def testAgentSearchCLI_WhenAuthenticatedRunner_listAgents(mocker, httpx_mock):
    """Test ostorlab agent search CLI command with Autenticated API returns list of agents."""
    mock.patch("ostorlab.api.runners.authenticated_runner")
    mocker.patch(
        "ostorlab.configuration_manager.ConfigurationManager.api_key",
        new_callable=mock.PropertyMock,
        return_value="test",
    )
    agents_dict = {
        "data": {
            "agents": {
                "agents": [
                    {
                        "key": "agent/jiji/ssss",
                        "versions": {
                            "versions": [
                                {
                                    "key": "agent/jiji/ssss:0.0.2",
                                    "version": "0.0.2",
                                    "description": "ssss",
                                    "inSelectors": ["/file"],
                                    "outSelectors": ["/vuln"],
                                }
                            ]
                        },
                    }
                ]
            }
        }
    }
    httpx_mock.add_response(
        method="POST",
        url=authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=agents_dict,
        status_code=200,
    )
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ["agent", "search", "-k", "xss"])

    assert "Found 1 Agents" in result.output
    assert "agent/jiji/ssss" in result.output
    assert "vuln" in result.output


def testAgentSearchCLI_WhenPublicRunner_listAgents(mocker, httpx_mock):
    """Test ostorlab agent search CLI command with Public API returns list of agents."""
    agents_dict = {
        "data": {
            "agents": {
                "agents": [
                    {
                        "key": "agent/jiji/ssss",
                        "versions": {
                            "versions": [
                                {
                                    "key": "agent/jiji/ssss:0.0.2",
                                    "version": "0.0.2",
                                    "description": "ssss",
                                    "inSelectors": ["/file"],
                                    "outSelectors": ["/vuln"],
                                }
                            ]
                        },
                    }
                ]
            }
        }
    }

    httpx_mock.add_response(
        method="POST",
        url=public_runner.PUBLIC_GRAPHQL_ENDPOINT,
        json=agents_dict,
        status_code=200,
    )
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ["agent", "search", "-k", "xss"])

    assert "Found 1 Agents" in result.output
    assert "agent/jiji/ssss" in result.output
    assert "vuln" in result.output
