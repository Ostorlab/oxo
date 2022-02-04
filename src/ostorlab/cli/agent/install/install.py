"""Ostorlab CLI agent install command."""

import click

from ostorlab.cli.agent import agent
from ostorlab.cli import console as cli_console
from ostorlab.cli import install_agent


console = cli_console.Console()


@agent.command()
@click.option('--agent_key', '-key', help='Agent key.', required=True)
@click.option('--tag', '-tag', help='Agent tag.', required=False)
def install(agent_key: str, tag: str = '') -> None:
    """CLI command to install an agent : Fetch the docker file location of the agent corresponding to the agent_key,
    and pull the image from the registry.
    Usage : ostorlab agent install --agent_key=<agent_key> --tag=<tag>
    """

    install_agent.install(agent_key, tag)
