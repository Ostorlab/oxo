"""Unit tests for the ostorlab scanner subcommand."""
from click.testing import CliRunner

from ostorlab.cli import rootcli


def testRootCli_whenDaemonCommandIsProvided_runsBackground(mocker, requests_mock):
    """Run CLI with daemon command."""
    daemon_context_open = mocker.patch("daemon.DaemonContext.open", return_value=None)
    mocker.patch("ostorlab.cli.scanner.scanner", return_value=None)
    runner = CliRunner()
    runner.invoke(
        rootcli.rootcli,
        ["--api-key", "test", "scanner", "--daemon", "--scanner-id", "11226DS"],
    )
    assert daemon_context_open.call_count == 1
