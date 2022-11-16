"""Tests for scan run android-aab command."""
from click.testing import CliRunner

from ostorlab.cli import rootcli


def testScanRunAndroidAab_whenNoOptionsProvided_shouldExitAndShowError(mocker):
    """Test ostorlab scan run android-aab command with no options and no sub command.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch('ostorlab.runtimes.local.LocalRuntime.__init__', return_value=None)
    mocker.patch('ostorlab.runtimes.local.LocalRuntime.can_run', return_value=True)
    result = runner.invoke(rootcli.rootcli, ['scan', 'run', '--agent=agent1 --agent=agent2', 'android-aab'])

    assert 'Command missing either file path or source url of the aab file.' in result.output
    assert result.exit_code == 2


def testScanRunAndroidAab_whenBothFileAndUrlOptionsAreProvided_shouldExitAndShowError(mocker):
    """Test ostorlab scan run android-aab command when both file & url options are provided.
    Should show error message and exit with exit_code = 2."""

    runner = CliRunner()
    mocker.patch('ostorlab.runtimes.local.LocalRuntime.__init__', return_value=None)
    mocker.patch('ostorlab.runtimes.local.LocalRuntime.can_run', return_value=True)
    command=['scan', 'run', '--agent=agent1', 'android-aab', '--file', 'android_aab_test.py', '--url', 'url1']
    result = runner.invoke(rootcli.rootcli, command)

    assert 'Command accepts either path or source url of the aab file.' in result.output
    assert result.exit_code == 2
