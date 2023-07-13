"""Tests for scan run ios-ipa command."""
from click.testing import CliRunner

from ostorlab.cli import rootcli


def testScanRunIosIpa_whenNoOptionsProvided_shouldExitAndShowError(mocker):
    """Test ostorlab scan run ios-ipa command with no options and no sub command.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli, ["scan", "run", "--agent=agent1 --agent=agent2", "ios-ipa"]
    )

    assert (
        "Command missing either file path or source url of the ipa file."
        in result.output
    )
    assert result.exit_code == 2


def testScanRunIosIpa_whenBothFileAndUrlOptionsAreProvided_shouldExitAndShowError(
    mocker,
):
    """Test ostorlab scan run ios-ipa command when both file & url options are provided.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    command = [
        "scan",
        "run",
        "--agent=agent1",
        "ios-ipa",
        "--file",
        "tests/__init__.py",
        "--url",
        "url1",
    ]
    result = runner.invoke(rootcli.rootcli, command)

    assert result.exit_code == 2
