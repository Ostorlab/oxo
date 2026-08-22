"""Tests for scan run harmonyos-apk command."""

from click.testing import CliRunner

from ostorlab.cli import rootcli


def testScanRunHarmonyOSApk_whenNoOptionsProvided_shouldExitAndShowError(mocker):
    """Test oxo scan run harmonyos-apk command with no options and no sub command.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1 --agent=agent2", "harmonyos-apk"],
    )

    assert (
        "Command missing either file path or source url of the apk file."
        in result.output
    )
    assert result.exit_code == 2


def testScanRunHarmonyOSApk_whenBothFileAndUrlOptionsAreProvided_shouldExitAndShowError(
    mocker,
):
    """Test oxo scan run harmonyos-apk command when both file & url options are provided.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    command = [
        "scan",
        "run",
        "--agent=agent1",
        "harmonyos-apk",
        "--file",
        "tests/__init__.py",
        "--url",
        "url1",
    ]
    result = runner.invoke(rootcli.rootcli, command)

    assert result.exit_code == 2
