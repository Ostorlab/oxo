"""Tests for CLI agent build command."""

import pathlib

import docker
import pytest
from click import testing

from ostorlab.cli import rootcli
from ostorlab.cli.agent.build import build as agent_build


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


def testAgentBuildCLI_whenBuildRootIsConfigured_useAgentDefinitionDirectory(
    mocker,
):
    """Resolve the configured Docker build root from the agent definition."""
    dummy_def_yaml_file_path = (
        pathlib.Path(__file__).parent / "assets/nested_build_root_dummydef.yaml"
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_installed",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_user_permitted",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working",
        return_value=True,
    )
    mocker.patch.object(agent_build, "_image_exists", return_value=False)
    mocker.patch.object(agent_build.docker, "from_env")
    build_image = mocker.patch.object(agent_build, "_build_image")
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

    assert result.exit_code == 0
    assert build_image.call_args.args[3] == str(
        (dummy_def_yaml_file_path.parent / "build_context").resolve()
    )


def testAgentBuildCLI_whenParentBuildRootPath_failShowErrorMessage():
    """Reject a Docker build root outside the agent definition directory."""
    dummy_def_yaml_file_path = (
        pathlib.Path(__file__).parent / "assets/illegal_build_root_dummydef.yaml"
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
    dummy_def_yaml_file_path = pathlib.Path(__file__).parent / "assets/dummydef.yaml"
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
    dummy_def_yaml_file_path = pathlib.Path(__file__).parent / "assets/dummydef.yaml"
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
    dummy_def_yaml_file_path = pathlib.Path(__file__).parent / "assets/dummydef.yaml"
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


def testAgentBuildCLI_whenAgentDefinitionHasInvalidArgType_failShowErrorMessage() -> (
    None
):
    """Test oxo agent build CLI command : Case where the agent definition file has an invalid arg type."""
    invalid_agent_def = pathlib.Path(__file__).parent / "assets/invalid_agent_def.yaml"
    runner = testing.CliRunner()

    result = runner.invoke(
        rootcli.rootcli,
        [
            "agent",
            "build",
            f"--file={invalid_agent_def}",
            "--organization=ostorlab",
        ],
    )

    assert result.output == (
        "🔺 ERROR: Definition file does not conform to the provided specification: \n"
        "Validation did not pass: 'test' is not one of ['string', 'number', "
        "'boolean', \n"
        "'array', 'object'] for field properties.args.items.properties.type.enum.\n"
    )
