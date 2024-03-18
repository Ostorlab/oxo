"""Tests for CLI agent build command."""

from pathlib import Path

import docker
import pytest
from click import testing

from ostorlab.cli import rootcli


def testAgentBuildCLI_whenRequiredOptionFileIsMissing_showMessage():
    """Test oxo agent build CLI command without the required file option. Should show help message, and confirm
    the --file option is missing.
    """
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ["agent", "build"])

    assert "Usage: rootcli agent build [OPTIONS]" in result.output
    assert "Try 'rootcli agent build --help' for help." in result.output
    assert "Error: Missing option '--file' / '-f'." in result.output


def _is_docker_image_present(image: str):
    docker_sdk_client = docker.from_env()
    try:
        docker_sdk_client.images.get(image)
        return True
    except docker.errors.ImageNotFound:
        return False


def testAgentBuildCLI_whenParentBuildRootPath_failShowErrorMessage():
    """Test oxo agent build CLI command : Case where the command is valid. The agent container should be built."""
    dummy_def_yaml_file_path = (
        Path(__file__).parent / "assets/illegal_build_root_dummydef.yaml"
    )
    runner = testing.CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "agent",
            "build",
            f"--file={dummy_def_yaml_file_path}",
            "--organization=ostorlab",
        ],
    )
    assert "ERROR: Invalid docker build path" in result.output


@pytest.mark.docker
@pytest.mark.parametrize("image_cleanup", ["dummy"], indirect=True)
def testAgentBuildCLI_whenCommandIsValid_buildCompletedAndNoRaiseImageNotFoundExcep(
    image_cleanup,
):
    """Test oxo agent build CLI command : Case where the command is valid. The agent container should be built."""
    del image_cleanup
    dummy_def_yaml_file_path = Path(__file__).parent / "assets/dummydef.yaml"
    runner = testing.CliRunner()
    _ = runner.invoke(
        rootcli.rootcli,
        [
            "agent",
            "build",
            f"--file={dummy_def_yaml_file_path}",
            "--organization=ostorlab",
        ],
    )
    assert _is_docker_image_present("agent_ostorlab_dummy_agent:v1.0.0") is True


@pytest.mark.docker
@pytest.mark.parametrize("image_cleanup", ["dummy"], indirect=True)
def testAgentBuildCLI_whenCommandIsValidAndImageAlreadyExists_showsMessageAndExists(
    image_cleanup,
):
    """Test oxo agent build CLI command : Case where the command is valid. The agent container should be built."""
    del image_cleanup
    dummy_def_yaml_file_path = Path(__file__).parent / "assets/dummydef.yaml"
    runner = testing.CliRunner()
    _ = runner.invoke(
        rootcli.rootcli,
        [
            "agent",
            "build",
            f"--file={dummy_def_yaml_file_path}",
            "--organization=ostorlab",
        ],
    )
    result = runner.invoke(
        rootcli.rootcli,
        [
            "agent",
            "build",
            f"--file={dummy_def_yaml_file_path}",
            "--organization=ostorlab",
        ],
    )
    assert "already exist" in result.output
    assert result.exit_code == 0


@pytest.mark.docker
@pytest.mark.parametrize("image_cleanup", ["dummy"], indirect=True)
def testAgentBuildCLI_whenImageAlreadyExistsAndForceFlagPassed_buildCompletedAndNoRaiseImageNotFoundExcep(
    image_cleanup,
):
    """Test oxo agent build CLI command : Case where the command is valid, the image exists and force flag is
    passed. The agent container should be built.
    """
    del image_cleanup
    dummy_def_yaml_file_path = Path(__file__).parent / "assets/dummydef.yaml"
    runner = testing.CliRunner()
    _ = runner.invoke(
        rootcli.rootcli,
        [
            "agent",
            "build",
            f"--file={dummy_def_yaml_file_path}",
            "--organization=ostorlab",
        ],
    )
    result = runner.invoke(
        rootcli.rootcli,
        [
            "agent",
            "build",
            "--force",
            f"--file={dummy_def_yaml_file_path}",
            "--organization=ostorlab",
        ],
    )
    assert "already exist" not in result.output
    assert result.exit_code == 0
