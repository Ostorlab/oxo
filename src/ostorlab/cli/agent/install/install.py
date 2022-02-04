"""Ostorlab CLI agent install command."""

import click

from ostorlab.cli.agent import agent
from ostorlab.cli import console as cli_console
from ostorlab.cli import install_agent


console = cli_console.Console()


@agent.command()
@click.option('--agent', '-a', help='Agent key.', required=True)
@click.option('--version', '-v', help='Agent version.', required=False)
def install(agent: str, version: str = '') -> None:
    """CLI command to install an agent : Fetch the docker file location of the agent corresponding to the agent_key,
    and pull the image from the registry.
    """
    install_agent.install(agent, version)
