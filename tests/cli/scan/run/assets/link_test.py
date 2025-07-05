"""Tests for scan run link command."""

from click.testing import CliRunner

from ostorlab.cli import rootcli


def testScanRunLink_whenNoOptionsProvided_showsAvailableOptionsAndCommands(mocker):
    """Test oxo scan run link command with no options and no sub command.
    Should show list of available commands and exit with exit_code = 0."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli, ["scan", "run", "--agent=agent1 --agent=agent2", "link"]
    )

    assert "Usage:" in result.output
    assert result.exit_code == 2


def testRunScanLink_whenValidAgentsAreProvidedWithNoAsset_ShowSpecifySubCommandError(
    mocker,
):
    """Test oxo scan run link with non-supported runtime, should exit with return code 1."""

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
            "link",
            "--url",
            "https://ostorlab.co",
            "--method",
            "GET",
        ],
    )

    assert "Usage:" not in result.output
    assert isinstance(result.exception, SystemExit)
    assert result.exit_code == 1


def testRunScanLink_withHeaderAndCookie_ShowSpecifySubCommandError(
    mocker,
) -> None:
    """Test oxo scan run link with non-supported runtime, should exit with return code 1."""

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
            "link",
            "--url",
            "https://ostorlab.co",
            "--method",
            "GET",
            "--cookie",
            "cookie1=123--cookie",
            "cookie2=456",
            "--header",
            "header1=123",
        ],
    )

    assert "Usage:" not in result.output
    assert isinstance(result.exception, SystemExit)
    assert result.exit_code == 1
