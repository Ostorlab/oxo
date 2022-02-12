"""Ostorlab CLI agent install command."""

import click

from ostorlab.cli.agent import agent as agent_command
from ostorlab.cli import console as cli_console
from ostorlab.cli import install_agent
from ostorlab.cli import docker_requirements_checker


console = cli_console.Console()


@agent_command.command()
@click.option('--agent', '-a', help='Agent key.', required=True)
@click.option('--version', '-v', help='Agent version.', required=False)
def install(agent: str, version: str = '') -> None:
    """Install an agent : pull the image from the ostorlab store."""

    if not docker_requirements_checker.is_docker_installed():
        console.error('Docker is not installed.')
        raise click.exceptions.Exit(2)
    elif not docker_requirements_checker.is_user_permitted():
        console.error('User does not have permissions to run docker.')
        raise click.exceptions.Exit(2)
    else:
        install_agent.install(agent, version)
