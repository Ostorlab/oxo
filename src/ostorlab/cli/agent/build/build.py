'""Agent Build commands.""'
import io
import pathlib
import logging

import click
import docker
import ruamel.yaml

from ostorlab.cli.agent import agent
from ostorlab.agent.schema import validator

AGENT_SPEC_PATH = pathlib.Path(__file__).parent.parent.parent.parent / 'agent/schema/agent_schema.json'
logger = logging.getLogger(__name__)


@agent.command()
@click.option('--file', '-f', type=click.File('rb'), help='Path to Agent yaml definition.', required=True)
def build(file: io.FileIO) -> None:
    """CLI command to build the agent container from a definition.yaml file.
    Usage : Ostorlab agent build -f path/to/definition.yaml
    """

    with open(AGENT_SPEC_PATH, 'r', encoding='utf8') as agent_spec:
        try:
            yaml_def_validator = validator.Validator(agent_spec)
        except validator.SchemaError:
            logger.error('Schema is invalid.')

    try:
        yaml_def_validator.validate(file)
        file.seek(0)
        yaml = ruamel.yaml.YAML(typ='safe')
        agent_def = yaml.load(file)

        dockerfile_path = agent_def['docker_file_path']
        docker_build_root = agent_def['docker_build_root']
        container_name = agent_def['name']

        docker_sdk_client = docker.from_env()
        docker_sdk_client.images.build(path=docker_build_root, dockerfile=dockerfile_path, tag=container_name)
    except validator.ValidationError:
        logger.error('Definition file does not conform to the provided specification.')

