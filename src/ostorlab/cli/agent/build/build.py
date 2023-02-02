"""Agent Build commands."""
import io
import logging
import pathlib

import click
import docker
from docker import errors

from ostorlab.agent.schema import loader
from ostorlab.agent.schema import validator
from ostorlab.cli import console as cli_console
from ostorlab.cli import docker_requirements_checker
from ostorlab.cli.agent import agent
from ostorlab.cli.agent.build import build_progress

console = cli_console.Console()

logger = logging.getLogger(__name__)


def _image_exists(image: str) -> bool:
    """Checks if container images exists."""
    try:
        docker_sdk_client = docker.from_env()
        docker_sdk_client.images.get(image)
        return True
    except docker.errors.ImageNotFound:
        return False


def _build_image(
    agent_name: str,
    container_name: str,
    dockerfile_path: str,
    docker_build_root: str,
    agent_definition_file: io.FileIO,
    no_cache: bool,
) -> None:
    """Build agent image from agent settings."""
    console.info(
        f"Building agent [bold red]{agent_name}[/] dockerfile [bold red]{dockerfile_path}[/]"
        f" at root [bold red]{docker_build_root}[/]."
    )
    with console.status(f"Building [bold red]{container_name}[/]"):
        for log in build_progress.BuildProgress().build(
            path=docker_build_root,
            dockerfile=dockerfile_path,
            tag=container_name,
            labels={"agent_definition": agent_definition_file.read().decode("utf-8")},
            nocache=no_cache,
        ):
            if "stream" in log and log["stream"] != "\n":
                console.info(log["stream"][:-1])
            elif "error" in log:
                console.error(log["error"][:-1])
            else:
                logger.debug(log)

    console.success(
        f"Agent {agent_name} built, container [bold red]{container_name}[/] created."
    )


@agent.command()
@click.option(
    "--file",
    "-f",
    type=click.File("rb"),
    help="Path to Agent yaml definition.",
    required=True,
)
@click.option(
    "--organization", "-o", help="Organization name.", required=False, default=""
)
@click.option("--force/--no-force", default=False)
@click.option("--no-cache", is_flag=True, default=False)
def build(
    file: io.FileIO, organization: str = "", force: bool = False, no_cache: bool = False
) -> None:
    """CLI command to build the agent container from a definition.yaml file.
    Usage : Ostorlab agent build -f path/to/definition.yaml -org organization_name
    """

    if not docker_requirements_checker.is_docker_installed():
        console.error("Docker is not installed.")
        raise click.exceptions.Exit(2)
    if not docker_requirements_checker.is_user_permitted():
        console.error("User does not have permissions to run docker.")
        raise click.exceptions.Exit(2)
    if not docker_requirements_checker.is_docker_working():
        console.error("Error using docker.")
        raise click.exceptions.Exit(2)

    try:
        agent_def = loader.load_agent_yaml(file)
        file.seek(0)
        dockerfile_path = agent_def["docker_file_path"]
        docker_build_root = agent_def["docker_build_root"]

        _check_build_root(docker_build_root, file)

        agent_name = agent_def["name"]
        agent_version = agent_def.get("version", "0.0.0")
        container_name = f"agent_{organization}_{agent_name}:v{agent_version}"
        client = docker.from_env()

        if _image_exists(container_name):
            if force is False:
                console.info(f"{container_name} already exist.")
                raise click.exceptions.Exit(0)
            else:
                console.warning(f"{container_name} already exist, deleting image.")
                client.images.remove(container_name, force=True)
        _build_image(
            agent_name,
            container_name,
            dockerfile_path,
            docker_build_root,
            file,
            no_cache,
        )

    except errors.BuildError as e:
        console.error("Error building agent.")
        raise click.exceptions.Exit(2) from e
    except validator.SchemaError as e:
        console.error(
            "Schema is invalid, this should not happen, please report an issue at "
            "https://github.com/Ostorlab/ostorlab/issues."
        )
        raise click.exceptions.Exit(2) from e
    except validator.ValidationError as e:
        console.error("Definition file does not conform to the provided specification.")
        raise click.exceptions.Exit(2) from e


def _check_build_root(docker_build_root, file):
    """Check whether build root is valid.

    Checks if docker build root is a subfolder of yaml file path.
    """
    yaml_file_dir = pathlib.Path(file.name).parent.resolve()
    docker_build_root_path = (yaml_file_dir / docker_build_root).resolve()
    if str(yaml_file_dir) not in str(docker_build_root_path):
        console.error(f"Invalid docker build path {docker_build_root}.")
        raise click.exceptions.Exit(3)
