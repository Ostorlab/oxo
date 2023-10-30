"""Tests for scan run command."""
import requests
import pytest

from click.testing import CliRunner

from ostorlab.cli import rootcli


def testOstorlabScanRunCLI_whenNoOptionsProvided_showsAvailableOptionsAndCommands(
    mocker,
):
    """Test ostorlab scan command with no options and no sub command.
    Should show list of available commands and exit with exit_code = 0."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    result = runner.invoke(rootcli.rootcli, ["scan", "run"])
    assert "Usage: rootcli scan run [OPTIONS] COMMAND [ARGS]..." in result.output
    assert "Commands:" in result.output
    assert "Options:" in result.output
    assert result.exit_code == 2


def testRunScanCLI_WhenAgentsAreInvalid_ShowError(mocker):
    """Test ostorlab scan command with all options and no sub command.
    Should show list of available commands (assets) and exit with error exit_code = 2.
    """

    mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.can_run", return_value=False
    )
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "--runtime=local",
            "run",
            "--agent=agent1",
            "--title=scan1",
            "android-apk",
        ],
    )

    assert isinstance(result.exception, BaseException)


@pytest.mark.docker
def testRunScanCLI_WhenNoConnection_ShowError(mocker):
    """Test ostorlab scan command with all options and no sub command.
    Should show list of available commands (assets) and exit with error exit_code = 2.
    """

    mocker.patch(
        "ostorlab.runtimes.cloud.runtime.CloudRuntime.can_run", return_value=True
    )
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.install",
        side_effect=requests.exceptions.ConnectionError("No internet connection"),
    )
    api_ubjson_requests = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute_ubjson_request"
    )

    api_requests = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute"
    )
    agent_details_reponse = {
        "data": {
            "agent": {
                "name": "whatweb",
                "gitLocation": "https://github.com/Ostorlab/agent_whatweb",
                "yamlFileLocation": "ostorlab.yaml",
                "dockerLocation": "ostorlab.store/agents/agent_5448_whatweb",
                "access": "PUBLIC",
                "listable": True,
                "key": "agent/ostorlab/whatweb",
                "versions": {"versions": [{"version": "0.1.12"}]},
            }
        }
    }

    agent_group_response = {"data": {"publishAgentGroup": {"agentGroup": {"id": "1"}}}}
    asset_response = {"data": {"createAsset": {"asset": {"id": 1}}}}
    scan_response = {"data": {"createAgentScan": {"scan": {"id": 1}}}}
    api_responses = [
        agent_details_reponse,
        asset_response,
        scan_response,
    ]
    api_ubjson_responses = [
        agent_group_response,
    ]

    api_requests.side_effect = api_responses
    api_ubjson_requests.side_effect = api_ubjson_responses
    runner = CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "--runtime=local",
            "run",
            "--install",
            "--agent=agent/ostorlab/nmap",
            "--title=scan1",
            "ip",
            "127.0.0.1",
        ],
    )
    assert (
        "Error: Could not install the agents: No internet connection\n" in result.output
    )
    assert result.exit_code == 1


def testRunScanCLI__whenValidAgentsAreProvidedWithNoAsset_ShowSpecifySubCommandError(
    mocker,
):
    """Test ostorlab scan run command with all valid options and no sub command.
    Should show list of available commands (assets) and exit with error exit_code = 2.
    """

    mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.can_run", return_value=True
    )
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "--runtime=local",
            "run",
            "--agent=agent1 --agent=agent2",
            "--title=scan1",
        ],
    )

    assert "Error: Missing command." in result.output
    assert result.exit_code == 2


def testScanRunCloudRuntime_whenValidArgsAreProvided_CreatesAgGrAssetAndScan(mocker):
    """Unittest ostorlab scan run in cloud runtime with all valid options and arguments.
    Should send api requests for creating Agent group, asset & scan.
    And displays Scan created successfully.
    """

    mocker.patch(
        "ostorlab.runtimes.cloud.runtime.CloudRuntime.can_run", return_value=True
    )

    api_ubjson_requests = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute_ubjson_request"
    )

    api_requests = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute"
    )
    agent_details_reponse = {
        "data": {
            "agent": {
                "name": "nmap",
                "gitLocation": "https://github.com/Ostorlab/agent_whatweb",
                "yamlFileLocation": "ostorlab.yaml",
                "dockerLocation": "ostorlab.store/agents/agent_5448_nmap",
                "access": "PUBLIC",
                "listable": True,
                "key": "agent/ostorlab/nmap",
                "versions": {"versions": [{"version": "0.1.12"}]},
            }
        }
    }

    agent_group_response = {"data": {"publishAgentGroup": {"agentGroup": {"id": "1"}}}}
    asset_response = {"data": {"createAsset": {"asset": {"id": 1}}}}
    scan_response = {"data": {"createAgentScan": {"scan": {"id": 1}}}}
    api_responses = [
        agent_details_reponse,
        asset_response,
        scan_response,
    ]
    api_ubjson_responses = [
        agent_group_response,
    ]

    api_requests.side_effect = api_responses
    api_ubjson_requests.side_effect = api_ubjson_responses

    runner = CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "--runtime=cloud",
            "run",
            "--agent=agent/ostorlab/nmap",
            "--title=scan1",
            "ip",
            "127.0.0.1",
        ],
    )

    assert result.exception is None
    api_requests.assert_called()
    assert "Scan created successfully" in result.output


def testScanRunCloudRuntime_whenValidMultipleLinksGiven_CreatesAgGrAssetAndScan(mocker):
    """Unittest ostorlab scan run in cloud runtime with multiple links.
    Should send api requests for creating Agent group, asset & scan.
    And displays Scan created successfully.
    """

    mocker.patch(
        "ostorlab.runtimes.cloud.runtime.CloudRuntime.can_run", return_value=True
    )

    api_ubjson_requests = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute_ubjson_request"
    )

    api_requests = mocker.patch(
        "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute"
    )
    agent_details_reponse = {
        "data": {
            "agent": {
                "name": "whatweb",
                "gitLocation": "https://github.com/Ostorlab/agent_whatweb",
                "yamlFileLocation": "ostorlab.yaml",
                "dockerLocation": "ostorlab.store/agents/agent_5448_whatweb",
                "access": "PUBLIC",
                "listable": True,
                "key": "agent/ostorlab/whatweb",
                "versions": {"versions": [{"version": "0.1.12"}]},
            }
        }
    }

    agent_group_response = {"data": {"publishAgentGroup": {"agentGroup": {"id": "1"}}}}
    asset_response = {"data": {"createAsset": {"asset": {"id": 1}}}}
    scan_response = {"data": {"createAgentScan": {"scan": {"id": 1}}}}
    api_responses = [
        agent_details_reponse,
        asset_response,
        scan_response,
    ]
    api_ubjson_responses = [
        agent_group_response,
    ]

    api_requests.side_effect = api_responses
    api_ubjson_requests.side_effect = api_ubjson_responses
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "--runtime=cloud",
            "run",
            "--agent=agent1 --agent=agent2",
            "link",
            "--url",
            "https://ostorlab.co",
            "--method",
            "GET",
            "--url",
            "https://ostorlab.ma",
            "--method",
            "GET",
        ],
    )

    assert result.exception is None
    api_requests.assert_called()
    assert "Scan created successfully" in result.output


def testScanRun_whenNoAssetFlagWithInjectAssetSubCommand_raisesErrors(mocker):
    """Unittest to ensure scan run command fails when both --no-asset flag and
    inject asset sub-commands are provided."""
    mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.can_run", return_value=False
    )
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--no-asset",
            "--agent=agent1",
            "--title=scan1",
            "ip",
            "8.8.8.8",
        ],
    )

    assert "Sub-command ip specified with --no-asset flag." in result.output
