"""Tests for scan run ip command."""
from click.testing import CliRunner
from ostorlab.cli import rootcli


def testScanRunIp_whenNoOptionsProvided_showsAvailableOptionsAndCommands():
    """Test ostorlab scan run ip command with no options and no sub command.
    Should show list of available commands and exit with exit_code = 0."""

    runner = CliRunner()

    result = runner.invoke(rootcli.rootcli, ['scan', 'run', '--agents=agent1,agent2', 'ip'])

    assert 'Usage:' in result.output
    assert result.exit_code == 2


def testRunScanIp__whenValidAgentsAreProvidedWithNoAsset_ShowSpecifySubCommandError(mocker):
    """Test ostorlab scan run ip with non supported runtime, should exit with return code 1."""

    mocker.patch('ostorlab.runtimes.local.runtime.LocalRuntime.can_run', return_value=False)
    runner = CliRunner()
    mocker.patch('ostorlab.runtimes.local.LocalRuntime.__init__', return_value=None)
    result = runner.invoke(rootcli.rootcli,
                           ['scan', '--runtime=local', 'run', '--agent=agent1 --agent=agent2', 'ip', '192.168.1.1'])

    assert 'Usage:' not in result.output
    assert isinstance(result.exception, SystemExit)
    assert result.exit_code == 1
