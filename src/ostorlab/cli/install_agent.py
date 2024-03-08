"""Module responsible for installing an agent : Pulling the image from the ostorlab store."""

import logging
from typing import Dict, Optional, Generator

import click
import docker
import docker.errors

from ostorlab.cli import console as cli_console
from ostorlab.cli.agent.install import install_progress
from ostorlab.cli import agent_fetcher

logger = logging.getLogger(__name__)

console = cli_console.Console()


def _image_name_from_key(agent_key: str) -> str:
    """Generate docker image name from an agent key.

    Args:
        agent_key: agent key in the form agent/organization/name.

    Returns:
        image_name: image name in the form : agent_organization_name.
    """
    return agent_key.replace("/", "_").lower()


def _parse_repository_tag(repo_name: str, tag: str = None) -> tuple:
    """Get repo name and tag"""
    parts = repo_name.rsplit("@", 1)
    if len(parts) == 2:
        return tuple(parts)
    parts = repo_name.rsplit(":", 1)
    if len(parts) == 2 and "/" not in parts[1]:
        return tuple(parts)
    return repo_name, tag


def _pull_logs(
    docker_client: docker.DockerClient, repository: str, tag: Optional[str] = None
) -> Generator[Dict, None, None]:
    """Generate logs of the docker pull method."""
    repository, tag = _parse_repository_tag(repository, tag)
    pull_log = docker_client.api.pull(repository, tag=tag, stream=True, decode=True)
    for log in pull_log:
        yield log


def _get_image(
    docker_client: docker.DockerClient, repository: str, tag: str = None
) -> docker.models.images.Image:
    """Gets a docker image."""
    repository, tag = _parse_repository_tag(repository, tag)
    name = f"{repository}:{tag}"

    return docker_client.images.get(name)


def _is_image_present(docker_client: docker.DockerClient, image_name: str) -> bool:
    """Check if a docker image exists."""
    try:
        docker_client.images.get(image_name)
        return True
    except docker.errors.ImageNotFound:
        return False


def install(
    agent_key: str,
    version: str = "",
    docker_client: Optional[docker.DockerClient] = None,
) -> None:
    """Install an agent : Fetch the docker file location of the agent corresponding to the agent_key,
    and pull the image from the registry.

    Args:
        agent_key: key of the agent in agent/org/agentName format.
        version: version of the docker image.
        docker_client: optional instance of the docker client to use to install the agent.

    Returns:
        None

    Raises:
        click Exit exception with status code 2 when the docker image does not exist.
    """

    agent_details = agent_fetcher.get_details(agent_key)
    agent_docker_location = agent_details["dockerLocation"]
    if agent_docker_location is None or not agent_details.get("versions", {}).get(
        "versions", []
    ):
        console.error(f"Agent: {agent_key} image location is not yet available")
        raise click.exceptions.Exit(2)

    image_name = _image_name_from_key(agent_details["key"])
    expected_version = version or agent_details["versions"]["versions"][0]["version"]
    logger.debug("searching for image name %s", image_name)

    try:
        docker_client = docker_client or docker.from_env()

        if _is_image_present(docker_client, f"{image_name}:v{expected_version}"):
            console.info(f"{agent_key} already exist.")
        else:
            console.info(
                f"Pulling the image {agent_docker_location} from the ostorlab store."
            )
            pull_logs_generator = _pull_logs(
                docker_client, agent_docker_location, f"v{expected_version}"
            )

            agent_install_progress = install_progress.AgentInstallProgress()
            agent_install_progress.display(pull_logs_generator)

            agent_image = _get_image(
                docker_client=docker_client,
                repository=agent_docker_location,
                tag=f"v{expected_version}",
            )
            agent_image.tag(repository=image_name, tag=f"v{expected_version}")

    except docker.errors.ImageNotFound as e:
        error_message = f"Image of the provided agent : {agent_key} was not found."
        console.error(error_message)
        raise click.exceptions.Exit(2) from e
