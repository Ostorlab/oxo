"""Ostorlab CLI agent install command."""

import click

from ostorlab.cli import agent_fetcher
from ostorlab.cli.agent import agent as agent_command
from ostorlab.cli import console as cli_console
from ostorlab.cli import install_agent
from ostorlab.cli import docker_requirements_checker


console = cli_console.Console()


@agent_command.command()
@click.argument("agent", required=True)
@click.option("--version", "-v", help="Agent version.", required=False)
def install(agent: str, version: str = "") -> None:
    """Install an agent : pull the image from the ostorlab store."""

    if not docker_requirements_checker.is_docker_installed():
        console.error("Docker is not installed.")
        raise click.exceptions.Exit(2)
    elif not docker_requirements_checker.is_sys_arch_supported():
        console.error("System architecture is not supported.")
        raise click.exceptions.Exit(2)
    elif not docker_requirements_checker.is_user_permitted():
        console.error("User does not have permissions to run docker.")
        raise click.exceptions.Exit(2)
    elif not docker_requirements_checker.is_docker_working():
        console.error("Error using docker.")
        raise click.exceptions.Exit(2)
    else:
        try:
            install_agent.install(agent, version)
        except agent_fetcher.AgentDetailsNotFound as e:
            console.error(e)
            raise click.exceptions.Exit(2)
