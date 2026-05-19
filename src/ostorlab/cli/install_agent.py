"""Module responsible for installing an agent : Pulling the image from the ostorlab store."""

from __future__ import annotations

import logging
from typing import Generator

import click
import docker
import docker.errors
import tenacity
import datetime

from ostorlab.cli import console as cli_console
from ostorlab.cli.agent.install import install_progress
from ostorlab.cli import agent_fetcher
from ostorlab.apis import agent_download_token
from ostorlab.apis.runners import authenticated_runner

logger = logging.getLogger(__name__)

console = cli_console.Console(logger=logger)

RETRY_ATTEMPTS = 3
WAIT_TIME = datetime.timedelta(seconds=2)


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
    docker_client: docker.DockerClient,
    repository: str,
    tag: str | None = None,
    auth_config: dict[str, str] | None = None,
) -> Generator[dict, None, None]:
    """Generate logs of the docker pull method."""
    repository, tag = _parse_repository_tag(repository, tag)
    pull_log = docker_client.api.pull(
        repository, tag=tag, stream=True, decode=True, auth_config=auth_config
    )
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


def _fetch_download_token(agent_key: str, version: str | None, api_key: str) -> str:
    """Fetch a short-lived registry pull token for an agent image.

    Args:
        agent_key: agent key in agent/org/name format.
        version: optional version of the agent image.
        api_key: api key for authentication.

    Returns:
        The bearer token from the registry.
    """
    runner = authenticated_runner.AuthenticatedAPIRunner(api_key=api_key)
    response = runner.execute(
        agent_download_token.AgentDownloadTokenAPIRequest(agent_key, version)
    )
    errors = response.get("errors")
    if errors is not None:
        raise RuntimeError(f"GraphQL API returned errors: {errors}")
    data = response.get("data") or {}
    generate_token = data.get("generateAgentImageDownloadToken") or {}
    token = generate_token.get("token")
    if token is None:
        raise ValueError(f"Failed to retrieve installation token for agent {agent_key}")
    return token


@tenacity.retry(
    stop=tenacity.stop_after_attempt(RETRY_ATTEMPTS),
    wait=tenacity.wait_fixed(WAIT_TIME.total_seconds()),
    retry=tenacity.retry_if_exception_type(
        (docker.errors.APIError, docker.errors.DockerException)
    ),
    reraise=True,
)
def _do_install(
    docker_client: docker.DockerClient,
    agent_docker_location: str,
    tag: str,
    image_name: str,
    auth_config: dict[str, str] | None = None,
) -> None:
    """Pull the image and tag it."""
    console.info(f"Pulling the image {agent_docker_location} from the ostorlab store.")
    pull_logs_generator = _pull_logs(
        docker_client, agent_docker_location, tag, auth_config=auth_config
    )

    agent_install_progress = install_progress.AgentInstallProgress()
    agent_install_progress.display(pull_logs_generator)

    agent_image = _get_image(
        docker_client=docker_client,
        repository=agent_docker_location,
        tag=tag,
    )
    agent_image.tag(repository=image_name, tag=tag)


def install(
    agent_key: str,
    version: str = "",
    docker_client: docker.DockerClient | None = None,
    api_key: str | None = None,
) -> None:
    """Install an agent : Fetch the docker file location of the agent corresponding to the agent_key,
    and pull the image from the registry.

    Args:
        agent_key: key of the agent in agent/org/agentName format.
        version: version of the docker image.
        docker_client: optional instance of the docker client to use to install the agent.
        api_key: optional api key to fetch a short-lived download token for the image.

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

        if (
            _is_image_present(docker_client, f"{image_name}:v{expected_version}")
            is True
        ):
            console.info(f"{agent_key} already exist.")
        else:
            auth_config = None
            if api_key is not None:
                token = _fetch_download_token(
                    agent_key,
                    expected_version,
                    api_key,
                )
                auth_config = {"registrytoken": token}
            _do_install(
                docker_client,
                agent_docker_location,
                f"v{expected_version}",
                image_name,
                auth_config=auth_config,
            )

    except (docker.errors.APIError, docker.errors.DockerException) as e:
        error_message = f"An error was encountered while downloading the image of the {agent_key} agent."
        console.error(error_message)
        raise click.exceptions.Exit(2) from e
    except Exception as e:
        error_message = (
            f"An unexpected error occurred while installing {agent_key}: {e}"
        )
        console.error(error_message)
        raise click.exceptions.Exit(2) from e
