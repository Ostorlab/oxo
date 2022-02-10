"""Ostorlab CLI agent install command."""

import click

from ostorlab.cli.agent import agent as agent_command
from ostorlab.cli import console as cli_console
from ostorlab.cli import install_agent


console = cli_console.Console()


@agent_command.command()
@click.option('--agent', '-a', help='Agent key.', required=True)
@click.option('--version', '-v', help='Agent version.', required=False)
def install(agent: str, version: str = '') -> None:
    """Install an agent : pull the image from the ostorlab store."""
    install_agent.install(agent, version)
