"""Agent related CLI commands."""

import pathlib
import logging

import click
import docker
import ruamel.yaml

from ostorlab.cli import rootcli
from ostorlab.agent.schema import validator

# is it the correct way to do it ?
AGENT_SPEC_PATH = pathlib.Path(__file__).parent.parent.parent / "agent/schema/agent_schema.json"
logger = logging.getLogger(__name__)


@rootcli.agent.command()
@click.option("--file", "-f", help="Path to Agent yaml definition.", required=True)
def build(file):
    """Ostorlab agent build -f path/to/definition.yaml
    CLI command to build the agent container from a definition.yaml file.
    """
    with open(AGENT_SPEC_PATH, 'r', encoding='utf8') as agent_spec:
        try:
            yaml_def_validator = validator.Validator(agent_spec)
        except validator.SchemaError:
            logger.error("Schema is invalid.")

    try:
        yaml_def_validator.validate(file)
    except validator.ValidationError:
        logger.error("Definition file does not conform to the provided specification.")

    yaml = ruamel.yaml.YAML(typ='safe')
    with open(file, 'r', encoding='utf8') as def_file:
        agent_def = yaml.load(def_file)

    dockerfile_path = agent_def["docker_file_path"]
    docker_build_root = agent_def["docker_build_root"]
    container_name = agent_def["name"]

    docker_sdk_client = docker.from_env()
    docker_sdk_client.images.build(path=docker_build_root, dockerfile=dockerfile_path, tag= container_name)
