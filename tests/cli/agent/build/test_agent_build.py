"""Tests for CLI agent build command."""

import pytest

import docker
from click import testing

from ostorlab.cli import rootcli


def testAgentBuildCLI_whenRequiredOptionFileIsMissing_showMessage():
    """Test ostorlab agent build CLI command without the required file option.
    Should show help message, and confirm the --file option is missing.
    """
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ["agent", "build"])

    assert "Usage: rootcli agent build [OPTIONS]" in result.output
    assert "Try 'rootcli agent build --help' for help." in result.output
    assert "Error: Missing option '--file' / '-f'." in result.output


def testAgentBuildCLI_whenCommandIsValid_buildCompletedAndNoRaiseImageNotFoundExcep(docker_dummy_image_cleanup):
    """Test ostorlab agent build CLI command : Case where the command is valid.
    The agent container should be built.
    """
    dummy_def_yaml_file_path = "./assets/dummydef.yaml"
    runner = testing.CliRunner()
    _ = runner.invoke(rootcli.rootcli, ["agent", "build", f"--file={dummy_def_yaml_file_path}"])
    docker_sdk_client = docker.from_env()

    try:
        docker_sdk_client.images.get("dummy_agent")
    except docker.errors.ImageNotFound:
        pytest.fail("Docker ImageNotFound shouldn't be expected.")
