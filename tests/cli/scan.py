""" test for Ostorlab scan Cli """
from click.testing import CliRunner
from ostorlab.cli.rootcli import rootcli


def test_OstorlabScanCommand_WithNoparams_NoRaises():
    runner = CliRunner()
    result = runner.invoke(rootcli, ['scan'])
    assert not result.exception
