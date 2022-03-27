"""Tests for scan run domain-name command."""
from click.testing import CliRunner

from ostorlab.cli import rootcli


def testScanRunDomainName_whenNoOptionsProvided_showsAvailableOptionsAndCommands(mocker):
    """Test ostorlab scan run domain-name command with no options and no sub command.
    Should show list of available commands and exit with exit_code = 0."""

    runner = CliRunner()
    mocker.patch('ostorlab.runtimes.local.LocalRuntime.__init__', return_value=None)
    result = runner.invoke(rootcli.rootcli, ['scan', 'run', '--agents=agent1,agent2', 'domain-name'])

    assert 'Usage:' in result.output
    assert result.exit_code == 2


def testRunScanDomainName__whenValidAgentsAreProvidedWithNoAsset_ShowSpecifySubCommandError(mocker):
    """Test ostorlab scan run domain-name with non-supported runtime, should exit with return code 1."""

    mocker.patch('ostorlab.runtimes.local.runtime.LocalRuntime.can_run', return_value=False)
    runner = CliRunner()
    mocker.patch('ostorlab.runtimes.local.LocalRuntime.__init__', return_value=None)
    result = runner.invoke(rootcli.rootcli,
                           ['scan', '--runtime=local', 'run', '--agent=agent1 --agent=agent2', 'domain-name',
                            'ostorlab.co'])

    assert 'Usage:' not in result.output
    assert isinstance(result.exception, SystemExit)
    assert result.exit_code == 1
