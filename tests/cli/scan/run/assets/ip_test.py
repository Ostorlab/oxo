"""Tests for scan run ip command."""

from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab.cli import rootcli
from ostorlab.agent import definitions as agent_definitions


def testScanRunIp_whenNoOptionsProvided_showsAvailableOptionsAndCommands(mocker):
    """Test ostorlab scan run ip command with no options and no sub command.
    Should show list of available commands and exit with exit_code = 0."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli, ["scan", "run", "--agent=agent1 --agent=agent2", "ip"]
    )

    assert "Usage:" in result.output
    assert result.exit_code == 2


def testRunScanIp__whenValidAgentsAreProvidedWithNoAsset_ShowSpecifySubCommandError(
    mocker,
):
    """Test ostorlab scan run ip with non supported runtime, should exit with return code 1."""

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
            "--agent=agent1 --agent=agent2",
            "ip",
            "192.168.1.1",
        ],
    )

    assert "Usage:" not in result.output
    assert isinstance(result.exception, SystemExit)
    assert result.exit_code == 1


def testScanRunFile_whenPassedArgSupportedByTheAgent_callScanWithValidSettings(
    mocker: plugin.MockerFixture,
    nmap_agent_definition: agent_definitions.AgentDefinition,
) -> None:
    """Test ostorlab scan run ip command with valid arguments."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    mocker.patch(
        "ostorlab.cli.agent_fetcher.get_definition",
        return_value=nmap_agent_definition,
    )
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=True
    )

    runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "--arg=fast_mode:false",
            "ip",
            "8.8.8.8",
        ],
    )

    assert scan_mocked.call_count == 1
    color_arg = scan_mocked.call_args[1].get("agent_group_definition").agents[0].args[0]
    assert color_arg.value is False
    assert color_arg.name == "fast_mode"
    assert color_arg.type == "boolean"


def testScanRunFile_whenPassedArgIsNotSupportedByTheAgent_callScanWithValidSettings(
    mocker: plugin.MockerFixture,
    nmap_agent_definition: agent_definitions.AgentDefinition,
) -> None:
    """Test ostorlab scan run ip command with arguments not supported by the agent."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    mocker.patch(
        "ostorlab.cli.agent_fetcher.get_definition",
        return_value=nmap_agent_definition,
    )
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=True
    )

    runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "--arg=color:green",
            "ip",
            "8.8.8.8",
        ],
    )

    assert scan_mocked.call_count == 1
    assert (
        len(scan_mocked.call_args[1].get("agent_group_definition").agents[0].args) == 0
    )


def testScanRunFile_whenPassedArgIsOfTypeArrayAndSupportedByTheAgent_callScanWithValidSettings(
    mocker: plugin.MockerFixture,
    nmap_agent_definition: agent_definitions.AgentDefinition,
) -> None:
    """Test ostorlab scan run ip command with valid array argument."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    mocker.patch(
        "ostorlab.cli.agent_fetcher.get_definition",
        return_value=nmap_agent_definition,
    )
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=True
    )

    runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "--arg=scripts:script1,script2",
            "ip",
            "8.8.8.8",
        ],
    )

    assert scan_mocked.call_count == 1
    color_arg = scan_mocked.call_args[1].get("agent_group_definition").agents[0].args[0]
    assert color_arg.value == ["script1", "script2"]
    assert color_arg.name == "scripts"
    assert color_arg.type == "array"
