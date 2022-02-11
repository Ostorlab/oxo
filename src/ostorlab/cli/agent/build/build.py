"""Agent Build commands."""
import io
import logging

import click
import docker

from ostorlab.agent.schema import loader
from ostorlab.agent.schema import validator
from ostorlab.cli import console as cli_console
from ostorlab.cli.agent import agent
from ostorlab.cli import docker_requirements_checker

console = cli_console.Console()

logger = logging.getLogger(__name__)


@agent.command()
@click.option('--file', '-f', type=click.File('rb'), help='Path to Agent yaml definition.', required=True)
@click.option('--organization', '-o', help='Organization name.', required=False, default='')
def build(file: io.FileIO, organization: str = '') -> None:
    """CLI command to build the agent container from a definition.yaml file.
    Usage : Ostorlab agent build -f path/to/definition.yaml -org organization_name
    """

    if not docker_requirements_checker.is_docker_installed():
        console.error('Docker is not installed.')
        raise click.exceptions.Exit(2)
    elif not docker_requirements_checker.is_user_permitted():
        console.error('User does not have permissions to run docker.')
        raise click.exceptions.Exit(2)
    else:
        try:
            agent_def = loader.load_agent_yaml(file)
            dockerfile_path = agent_def['docker_file_path']
            docker_build_root = agent_def['docker_build_root']
            agent_name = agent_def['name']
            agent_version = agent_def.get('version', '0.0.0')
            console.info(
                f'Building agent [bold red]{agent_name}[/] dockerfile [bold red]{dockerfile_path}[/]'
                f' at root [bold red]{docker_build_root}[/].')
            container_name = f'agent_{organization}_{agent_name}:v{agent_version}'
            with console.status(f'Building [bold red]{container_name}[/]'):
                docker_sdk_client = docker.from_env()
                docker_sdk_client.images.build(path=docker_build_root, dockerfile=dockerfile_path, tag=container_name,
                                            labels={'agent_definition':file.read().decode('utf-8')})
            console.success(f'Agent {agent_name} built, container [bold red]{container_name}[/] created.')
        except validator.SchemaError:
            console.error(
                'Schema is invalid, this should not happen, please report an issue at '
                'https://github.com/Ostorlab/ostorlab/issues.')
        except validator.ValidationError:
            console.error('Definition file does not conform to the provided specification.')
