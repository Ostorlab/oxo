"""Tests for scan run harmonyos-aab command."""

from click.testing import CliRunner

from ostorlab.cli import rootcli


def testScanRunHarmonyOSAab_whenNoOptionsProvided_shouldExitAndShowError(mocker):
    """Test oxo scan run harmonyos-aab command with no options and no sub command.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1 --agent=agent2", "harmonyos-aab"],
    )

    assert (
        "Command missing either file path or source url of the aab file."
        in result.output
    )
    assert result.exit_code == 2


def testScanRunHarmonyOSAab_whenBothFileAndUrlOptionsAreProvided_shouldExitAndShowError(
    mocker,
):
    """Test oxo scan run harmonyos-aab command when both file & url options are provided.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    command = [
        "scan",
        "run",
        "--agent=agent1",
        "harmonyos-aab",
        "--file",
        "tests/__init__.py",
        "--url",
        "url1",
    ]
    result = runner.invoke(rootcli.rootcli, command)

    assert result.exit_code == 2
