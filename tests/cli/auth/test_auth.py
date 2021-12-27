"""Tests for auth login command."""
from click.testing import CliRunner, Result
from ostorlab.cli import rootcli
import requests_mock
from ostorlab.apis import runner


def testOstorlabAuthLoginCLI_whenNoOptionsProvided_showsAvailableOptionsAndCommands():
    """Test ostorlab auth login command with no options.
    Should usage."""

    runner = CliRunner()

    result = runner.invoke(rootcli.rootcli, ['auth', 'login'])

    assert 'Usage: rootcli auth login [OPTIONS]' in result.output
    assert result.exit_code == 2


def testOstorlabAuthLoginCLI_whenWrongCommandIsProvided_showsNoSuchCommandErrorAndExit():
    """Run CLI with wrong command.
    should show an error message and exit"""
    runner = CliRunner()

    result = runner.invoke(rootcli.rootcli, ['wrong-command'])

    assert "No such command 'wrong-command'" in result.output
    assert result.exit_code == 2


def testLogin_whenValidLoginare_propmt_OTP():
    click_runner = CliRunner()
    adapter = requests_mock.Adapter()
    adapter.register_uri(
        'POST', True, text="""{'non_field_errors':['Must include']}""", status_code=203)

    result = click_runner.invoke(
        rootcli.rootcli, ['auth', 'login', '--username=user', '-p=password'], input='123123\n')
    adapter.register_uri(
        'POST', True, text="""{'token':'kjhgfhgfytgfd'}""", status_code=200)

    assert isinstance(result.output, runner.AuthenticationError)
