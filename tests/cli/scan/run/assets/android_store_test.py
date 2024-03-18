"""Tests for scan runs android_store command."""

from click.testing import CliRunner

from ostorlab.cli import rootcli


def testScanRunAndroidStore_whenNoOptionsProvided_shouldExitAndShowError(mocker):
    """Test oxo scan run android-store command with no options and no sub command.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1 --agent=agent2", "android-store"],
    )

    assert "Command missing a package name." in result.output
    assert result.exit_code == 2


def testScanRunAndroidStore_whenOptionsProvided_shouldRunCommand(mocker):
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1 --agent=agent2",
            "android-store",
            "--package-name",
            "com.ariesapp.waiverforever",
        ],
    )

    assert "Creating scan entry" in result.output
