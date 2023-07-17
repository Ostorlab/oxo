"""Unit tests for the ostorlab scanner subcommand."""
import sys

import pytest
from click import testing as click_testing

from ostorlab.cli import rootcli


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def testRootCli_whenDaemonCommandIsProvided_runsBackground(mocker, requests_mock):
    """Run CLI with daemon command."""
    daemon_context_open = mocker.patch("daemon.DaemonContext.open", return_value=None)
    mocker.patch("ostorlab.cli.scanner.scanner", return_value=None)
    runner = click_testing.CliRunner()
    runner.invoke(
        rootcli.rootcli,
        ["--api-key", "test", "scanner", "--daemon", "--scanner-id", "11226DS"],
    )
    assert daemon_context_open.call_count == 1
