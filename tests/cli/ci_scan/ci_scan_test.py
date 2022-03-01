"""Tests for scan run command."""
from click.testing import CliRunner
from ostorlab.cli import rootcli


def testRunScanCLI_WhenAgentsAreInvalid_ShowError(mocker):
    """Test ostorlab scan command with all options and no sub command.
     Should show list of available commands (assets) and exit with error exit_code = 2."""

    mocker.patch('ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute', return_value=True)
    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli,
                           ['ci-scan', '--plan=free', '--type=android','--title=scan1', '--file=android-apk'])

    assert isinstance(result.exception, BaseException)


def testRunScanCLI__whenValidAgentsAreProvidedWithNoAsset(mocker):
    """Test ostorlab scan run command with all valid options and no sub command.
     Should show list of available commands (assets) and exit with error exit_code = 2."""

    mocker.patch('ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute', return_value=True)
    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli,
                           ['ci-scan', '--plan=free', '--type=android','--title=scan1', '--file=/tmp/gdm3-config-err-gfblTb', '--api_key=12'])

    assert 'Scan created.' in result.output
