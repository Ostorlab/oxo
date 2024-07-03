"""Tests for scan runs ios_store command."""

from click.testing import CliRunner

from ostorlab.cli import rootcli


def testScanRunIOSStore_whenNoOptionsProvided_shouldExitAndShowError(mocker):
    """Test oxo scan run ios-store command with no options and no sub command.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli, ["scan", "run", "--agent=agent1 --agent=agent2", "ios-store"]
    )

    assert "Command missing a bundle id." in result.output
    assert result.exit_code == 2


def testScanRunIOSStore_whenOptionsProvided_shouldRunCommand(mocker):
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1 --agent=agent2",
            "ios-store",
            "--bundle-id",
            "OWASP.iGoat-Swift",
        ],
    )

    assert "Creating network" in result.output
