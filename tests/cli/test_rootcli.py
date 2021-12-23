"""tests for ostorlab root cli"""
from click.testing import CliRunner
from ostorlab.cli import rootcli


def testRootCli_WithNoOptions_ShowAvailableOptions():
    """test ostorlab main command 'Ostorlab' with no options and no sub command."""
    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli, [''])
    assert "Usage: rootcli [OPTIONS]" in result.output
    assert result.exit_code == 2


def testRootCli_WrongCommand_ShowNoSuchCommandErrorAndExit():
    runner = CliRunner()
    result = runner.invoke(rootcli.rootcli, ['wrong-command'])
    assert "No such command 'wrong-command'" in result.output
    assert result.exit_code == 2
