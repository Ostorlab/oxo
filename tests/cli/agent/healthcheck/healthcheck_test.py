"""Tests for CLI agent healthcheck command."""

from click import testing

from ostorlab.cli import rootcli


def testAgentHealthcheckCLI_whenAgentIsNotHealthy_commandExitsWithError():
    """Test ostorlab agent healthcheck CLI command when healthcheck should fail."""
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ['agent', 'healthcheck'])

    assert 'ERROR: Error checking agent health' in result.output
    assert result.exit_code == 2


def testAgentHealthcheckCLI_whenAgentIsHealthy_commandExitsWithoutError():
    """Test ostorlab agent healthcheck CLI command when healthcheck should pass."""
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ['agent', 'healthcheck', '--host=google.com', '--port=80'])

    assert 'Response status code is 404' in result.output
    assert result.exit_code == 2
