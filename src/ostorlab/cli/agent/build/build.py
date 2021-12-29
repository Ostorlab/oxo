"""Agent Build commands."""
import io
import logging

import click
import docker

from ostorlab.agent.schema import loader
from ostorlab.agent.schema import validator
from ostorlab.cli.agent import agent

logger = logging.getLogger(__name__)


@agent.command()
@click.option('--file', '-f', type=click.File('rb'), help='Path to Agent yaml definition.', required=True)
def build(file: io.FileIO) -> None:
    """CLI command to build the agent container from a definition.yaml file.
    Usage : Ostorlab agent build -f path/to/definition.yaml
    """
    try:
        agent_def = loader.load_agent_yaml(file)

        dockerfile_path = agent_def['docker_file_path']
        docker_build_root = agent_def['docker_build_root']
        container_name = agent_def['name']

        docker_sdk_client = docker.from_env()
        docker_sdk_client.images.build(path=docker_build_root, dockerfile=dockerfile_path, tag=container_name)
    except validator.SchemaError:
        logger.error(
            'Schema is invalid, this should not happen, please report an issue at '
            'https://github.com/Ostorlab/ostorlab/issues.')
    except validator.ValidationError:
        logger.error('Definition file does not conform to the provided specification.')
