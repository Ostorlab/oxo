from click.testing import CliRunner
from ostorlab.cli.rootcli import rootcli


def test_RunScan():
    runner = CliRunner()
    result = runner.invoke(rootcli, ['scan'])
    assert not result.exception
