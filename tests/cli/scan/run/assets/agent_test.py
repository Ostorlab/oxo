"""Tests for scan run domain-name command."""
from click.testing import CliRunner

from ostorlab.cli import rootcli


def testScanRunAgent_whenNoOptionsProvided_showsAvailableOptionsAndCommands(mocker):
    """Test ostorlab scan run agent command with no options and no sub command.
    Should show list of available commands and exit with exit_code = 0."""

    runner = CliRunner()
    mocker.patch('ostorlab.runtimes.local.LocalRuntime.__init__', return_value=None)
    mocker.patch('ostorlab.runtimes.local.LocalRuntime.can_run', return_value=True)
    result = runner.invoke(rootcli.rootcli, ['scan', 'run', '--agent=agent1 --agent=agent2', 'agent'])

    assert 'Usage:' in result.output
    assert result.exit_code == 2


def testRunScanAgent__whenValidAgentsAreProvidedWithNoAsset_ShowSpecifySubCommandError(mocker):
    """Test ostorlab scan run agent with non-supported runtime, should exit with return code 1."""

    mocker.patch('ostorlab.runtimes.local.runtime.LocalRuntime.can_run', return_value=False)
    runner = CliRunner()
    mocker.patch('ostorlab.runtimes.local.LocalRuntime.__init__', return_value=None)
    result = runner.invoke(rootcli.rootcli,
                           ['scan', '--runtime=local', 'run', '--agent=agent1 --agent=agent2', 'agent',
                            '--key=agent/ostorlab/nmap', '--version=1.0.0',
                            '--git-location=https://github.com/Ostorlab/agent_nmap',
                            '--docker-location=ostorlab.store/agents/agent_5448_nmap',
                            '--yaml-file-location=ostorlab.yaml'
                            ])

    assert 'Usage:' not in result.output
    assert isinstance(result.exception, SystemExit)
    assert result.exit_code == 1
