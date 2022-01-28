"""Tests for CLI agent build command."""

from click import testing

from ostorlab.cli import rootcli


def testAgentHealthcheckCLI_whenAgentIsNotHealthy_commandExitsWithError():
    """Test ostorlab agent healthcheck CLI command when healthcheck should fail.
    """
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ['agent', 'healthcheck'])

    assert 'ERROR: Error checking agent health' in result.output
    assert result.exit_code == 2


def testAgentHealthcheckCLI_whenAgentIsHealthy_commandExitsWithoutError():
    """Test ostorlab agent healthcheck CLI command when healthcheck should pass.
    """
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ['agent', 'healthcheck', '--host=google.com', '--port=80'])

    assert 'ERROR: Error checking agent health' not in result.output
    assert result.exit_code == 0
