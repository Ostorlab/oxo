"""tests for ostorlab root cli"""
from click.testing import CliRunner
from ostorlab.cli import rootcli
import click


def testScanCli_WithNoOptions_ShowAvailableOptionsAndCommands():
    """Test ostorlab scan command with no options and no sub command.
    should show list of available commands and exit with exit_code = 0."""

    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli, ['scan'])
    assert "Usage: rootcli scan [OPTIONS] COMMAND [ARGS]..." in result.output
    assert "Commands:" in result.output
    assert "Options:" in result.output
    assert result.exit_code == 0


def testScanCli_WithInValidAgents_ShowError(mocker):
    """Test ostorlab scan command with all options and no sub command.
     should show list of available commands (assets) and exit with error exit_code = 2."""

    mocker.patch('src.ostorlab.runtimes.local.runtime.LocalRuntime.can_run', return_value=False)
    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli,
                           ['scan', '--agents=agent1,agent2', '--runtime=local', '--title=scan1', 'android-apk'])
    assert isinstance(result.exception, BaseException)


def testScanCli_WithValide_ShowSpecifySubCommandError(mocker):
    """Test ostorlab scan command with all options and no sub command.
     should show list of available commands (assets) and exit with error exit_code = 2."""

    mocker.patch('src.ostorlab.runtimes.local.runtime.LocalRuntime.can_run', return_value=True)
    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli, ['scan', '--agents=agent1,agent2', '--runtime=local', '--title=scan1'])
    assert "Error: Missing command." in result.output
    assert result.exit_code == 2
