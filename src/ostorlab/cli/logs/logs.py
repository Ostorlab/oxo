"""Module for the logs command.

This module takes care of streaming logs from running agent services.
Example of usage:
    - oxo logs --agent=agent/ostorlab/nmap
"""

import logging
from typing import Optional

import click
import docker

from ostorlab.cli import agent_fetcher
from ostorlab.cli import console as cli_console
from ostorlab.cli import types
from ostorlab.cli.rootcli import rootcli
from ostorlab.runtimes.local import log_streamer

console = cli_console.Console()
logger = logging.getLogger(__name__)


def _get_agent_image_name(agent_key: str) -> Optional[str]:
    """Get the container image name for an agent key.

    Args:
        agent_key: The agent key.

    Returns:
        The container image name without tag, or None if not found.
    """
    container_image = agent_fetcher.get_container_image(agent_key)
    if container_image is None:
        return None
    return container_image.split(":")[0]


def _find_services_by_agent_key(
    docker_client: docker.DockerClient, agent_key: str
) -> list[docker.models.services.Service]:
    """Find running docker services matching the agent key.

    Args:
        docker_client: Docker client instance.
        agent_key: The agent key to search for.

    Returns:
        List of matching docker services.
    """
    image_name = _get_agent_image_name(agent_key)
    if image_name is None:
        return []

    services = []
    for service in docker_client.services.list():
        try:
            service_image = service.attrs["Spec"]["TaskTemplate"]["ContainerSpec"][
                "Image"
            ]
            if (
                service_image.startswith(image_name + ":")
                or service_image.startswith(image_name + "@")
                or service_image == image_name
            ):
                services.append(service)
        except (KeyError, AttributeError):
            continue
    return services


@rootcli.command(name="logs")
@click.option(
    "--agent",
    help="Agent key to show logs for (agent/<org>/<name> or <org>/<name>). Org name can be omitted for defaults "
    "agent hosted by Ostorlab.",
    required=True,
    type=types.AgentKeyType(),
)
def logs(agent: str) -> None:
    """Show logs of a running agent.

    Usage:
        - oxo logs --agent=agent/ostorlab/nmap
    """
    docker_client = docker.from_env()
    services = _find_services_by_agent_key(docker_client, agent)

    if not services:
        console.error(f"No running services found for agent {agent}.")
        raise click.exceptions.Exit(1)

    log_stream = log_streamer.LogStream(docker_client)
    for service in services:
        log_stream.stream(service)

    console.info(f"Streaming logs for agent {agent}. Press Ctrl+C to stop.")
    try:
        log_stream.wait()
    except KeyboardInterrupt:
        console.info("Stopping log stream.")
