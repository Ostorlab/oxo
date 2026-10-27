"""Tests for CLI agent healthcheck command."""

import httpx
import pytest_httpx
from click import testing

from ostorlab.cli import rootcli


def testAgentHealthcheckCLI_whenAgentIsNotHealthy_commandExitsWithError(
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """Test oxo agent healthcheck CLI command when healthcheck should fail."""
    runner = testing.CliRunner()
    httpx_mock.add_exception(
        httpx.ConnectError("Connection refused"), url="http://localhost:5000/status"
    )

    result = runner.invoke(rootcli.rootcli, ["agent", "healthcheck"])

    assert "ERROR: Error checking agent health" in result.output
    assert result.exit_code == 2


def testAgentHealthcheckCLI_whenEndpointReturnsNotFound_commandExitsWithError(
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """Check the CLI reports non-success HTTP responses."""
    runner = testing.CliRunner()
    httpx_mock.add_response(url="http://agent.example:80/status", status_code=404)

    result = runner.invoke(
        rootcli.rootcli, ["agent", "healthcheck", "--host=agent.example", "--port=80"]
    )

    assert "Response status code is 404" in result.output
    assert result.exit_code == 2


def testAgentHealthcheckCLI_whenEndpointReturnsOK_commandExitsWithoutError(
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """Check the healthy HTTP response produces a successful CLI result."""
    httpx_mock.add_response(
        url="http://localhost:5000/status", status_code=200, text="OK"
    )
    result = testing.CliRunner().invoke(rootcli.rootcli, ["agent", "healthcheck"])
    assert result.exit_code == 0
    assert "Healthcheck OK on http://localhost:5000/status" in result.output
