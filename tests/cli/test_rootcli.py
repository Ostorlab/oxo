"""Tests for ostorlab root cli"""
import re

from click.testing import CliRunner

from ostorlab.cli import rootcli


def testRootCli_whenNoOptionProvided_showAvailableOptions():
    """Test ostorlab main command 'Ostorlab' with no options and no sub command.
    Should show list of available commands and options"""
    runner = CliRunner()

    result = runner.invoke(rootcli.rootcli, [""])

    assert "Usage: rootcli [OPTIONS]" in result.output
    assert result.exit_code == 2


def testRootCli_whenWrongCommandIsProvided_showsNoSuchCommandErrorAndExit():
    """Run CLI with wrong command.
    should show an error message and exit"""
    runner = CliRunner()

    result = runner.invoke(rootcli.rootcli, ["wrong-command"])

    assert "No such command 'wrong-command'" in result.output
    assert result.exit_code == 2


def testRootCli_whenDaemonCommandIsProvided_runsBackground(mocker, requests_mock):
    """Run CLI with daemon command."""
    matcher = re.compile(r"http\+docker://(.*)/version")
    requests_mock.get(matcher, json={"ApiVersion": "1.42"}, status_code=200)
    daemon_context_open = mocker.patch("daemon.DaemonContext.open", return_value=None)
    mocker.patch("ostorlab.cli.scan.list.list.list_scans", return_value=None)
    mocker.patch("ostorlab.cli.scan.scan", return_value=None)
    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli, ["--daemon", "scan", "list"])
    print(result)
    assert daemon_context_open.call_count == 1
