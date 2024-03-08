"""Module responsible for fetching the agent details from the container image."""

import logging
import io
from typing import Any, Optional
import re

import docker
import docker.errors

from ostorlab import configuration_manager
from ostorlab.apis import agent_details as agent_details_api
from ostorlab.apis.runners import public_runner, authenticated_runner
from ostorlab.apis.runners import runner as base_runner
from ostorlab.cli import console as cli_console
from ostorlab.agent import definitions as agent_definitions
from ostorlab.utils import version as version_definition

console = cli_console.Console()
logger = logging.getLogger(__name__)


class Error(Exception):
    """Base Error."""


class AgentDetailsNotFound(Error):
    """Agent not found error."""


def get_details(agent_key: str) -> dict[str, Any]:
    """Sends an API request with the agent key, and retrieve the agent information.

    Args:
        agent_key: the agent key in the form : agent/org/name

    Returns:
        dictionary of the agent information like : name, dockerLocation..

    Raises:
        AgentDetailsNotFound: If the agent is not found.
    """
    config_manager = configuration_manager.ConfigurationManager()

    if config_manager.is_authenticated is True:
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


def get_definition(
    agent_key: str,
) -> agent_definitions.AgentDefinition:
    """Fetch the agent definition.

    Args:
         agent_key: key of the agent in agent/org/agentName format.

    Returns:
        agent_definition: AgentDefinition object containing the agent definition.

    Raises:
         AgentDetailsNotFound: If the agent image is not found.
    """
    image_name = get_container_image(agent_key)
    if image_name is None:
        raise AgentDetailsNotFound(f"Agent {agent_key} not found")
    client = docker.from_env()
    docker_image = client.images.get(image_name)
    yaml_definition_string = docker_image.labels.get("agent_definition")
    with io.StringIO(yaml_definition_string) as file:
        agent_definition = agent_definitions.AgentDefinition.from_yaml(file)

    return agent_definition


def get_container_image(agent_key: str, version: Optional[str] = None) -> Optional[str]:
    """Get the agent container image name based on the agent key and optional version. If the version is not specified,
    the latest version is returned if found, otherwise, None is returned.

    Args:
        agent_key : The agent key.
        version : The version of the container image.

    Returns:
        The matching container image name with version. None if no matching image found.
    """
    image = agent_key.replace("/", "_")
    logger.debug("Searching container name %s with version %s", image, version)
    client = docker.from_env()
    matching_tag_versions = []
    for img in client.images.list(name=image):
        for t in img.tags:
            splitted_tag = t.split(":")
            if len(splitted_tag) == 2:
                t_name, t_tag = splitted_tag
            else:
                t_name = ":".join(splitted_tag[:-1])
                t_tag = splitted_tag[-1]
            if t_name == image and version is None:
                try:
                    matching_tag_versions.append(version_definition.Version(t_tag[1:]))
                except ValueError:
                    logger.warning("Invalid version %s", t_tag[1:])
            elif t_name == image and version is not None:
                if re.match(version, t_tag[1:]) is not None:
                    try:
                        matching_tag_versions.append(
                            version_definition.Version(t_tag[1:])
                        )
                    except ValueError:
                        logger.warning("Invalid version %s", t_tag[1:])

    if len(matching_tag_versions) == 0:
        return None

    matching_version = max(matching_tag_versions)
    return f"{image}:v{matching_version}"
