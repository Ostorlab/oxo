"""Module responsible for fetching the agent details from the container image."""

import logging
import io
from typing import Any

import click
import docker
import docker.errors

from ostorlab import configuration_manager
from ostorlab.apis import agent_details as agent_details_api
from ostorlab.apis.runners import public_runner, authenticated_runner
from ostorlab.apis.runners import runner as base_runner
from ostorlab.cli import console as cli_console
from ostorlab.agent import definitions as agent_definitions

logger = logging.getLogger(__name__)

console = cli_console.Console()


class Error(Exception):
    """Base Error."""


class AgentDetailsNotFound(Error):
    """Agent not found error."""


def get_agent_details(agent_key: str) -> dict[Any, Any]:
    """Sends an API request with the agent key, and retrieve the agent information.

    Args:
        agent_key: the agent key in the form : agent/org/name

    Returns:
        dictionary of the agent information like : name, dockerLocation..

    Raises:
        click Exit exception with satus code 2 when API response is invalid.
    """
    config_manager = configuration_manager.ConfigurationManager()

    if config_manager.is_authenticated:
        runner = authenticated_runner.AuthenticatedAPIRunner()
    else:
        runner = public_runner.PublicAPIRunner()

    try:
        response = runner.execute(agent_details_api.AgentDetailsAPIRequest(agent_key))
    except base_runner.ResponseError as e:
        raise AgentDetailsNotFound("requested agent not found") from e

    if "errors" in response:
        error_message = f"""The provided agent key : {agent_key} does not correspond to any agent.
        Please make sure you have the correct agent key.
        """
        raise AgentDetailsNotFound(error_message)
    else:
        agent_details = response["data"]["agent"]
        return agent_details


def get_agent_definition(
    agent_key: str,
) -> agent_definitions.AgentDefinition:
    """
    Fetch args of an agent from container image.
    """

    docker_client = docker.from_env()
    agent_details = get_agent_details(agent_key)
    agent_docker_location = agent_details["dockerLocation"]
    if agent_docker_location is None or not agent_details.get("versions", {}).get(
        "versions", []
    ):
        console.error(f"Agent: {agent_key} image location is not yet available")
        raise click.exceptions.Exit(2)

    image_name = f'{agent_details["key"].replace("/", "_")}:v{agent_details["versions"]["versions"][0]["version"]}'
    docker_image = docker_client.images.get(image_name)

    yaml_definition_string = docker_image.labels.get("agent_definition")
    with io.StringIO(yaml_definition_string) as file:
        agent_definition = agent_definitions.AgentDefinition.from_yaml(file)

    return agent_definition
