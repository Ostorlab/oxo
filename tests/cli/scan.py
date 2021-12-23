"""test for Ostorlab scan Cli"""
from click.testing import CliRunner

from ostorlab.cli.rootcli import rootcli


def testScanAndroidApk_WithApkFile_NoException(mocker):
    mocker.patch('ostorlab.runtimes.Runtime.can_run', return_value=True)

    runner = CliRunner()
    result = runner.invoke(rootcli, ['scan --agents=agent1,agent2 --runtime=local'])
    print(result)
    assert result.exception is NotImplementedError
