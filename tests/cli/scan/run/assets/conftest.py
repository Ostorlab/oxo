"""Shared fixtures for scan run asset tests."""

import pytest
from click import testing


@pytest.fixture
def scan_run_cli_runner(mocker):
    """Fixture providing a CliRunner with mocked local runtime."""
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    return testing.CliRunner()
