"""Agent List command."""
import logging
import re
from typing import Optional

import click
import docker

from ostorlab.cli import console as cli_console
from ostorlab.cli.agent import agent as agent_cli

console = cli_console.Console()

logger = logging.getLogger(__name__)


@agent_cli.command()
@click.argument('agent', required=True)
@click.option('--agent-version-regex', '-r', help='Agent version matching regular expression.', required=False)
def delete(agent: str, agent_version_regex: Optional[str] = None) -> None:
    """CLI command to delete installed agents."""
    docker_client = docker.from_env()
    images = docker_client.images.list()
    agent_container_name = agent.replace('/', '_')
    deleted = False
    for im in images:
        # If any tag match the agent key tag, we delete all tags. This is because images from the store downloaded with
        # store URL, and will cause the image to remain if we delete only one tag.
        if any(t.split(':')[0] == agent_container_name for t in im.tags):
            for t in im.tags:
                agent_container_version = t.split(':')[1]
                if agent_version_regex is None or re.match(agent_version_regex, agent_container_version):
                    console.info(f'deleting container [bold red]{t}[/]')
                    docker_client.images.remove(t, force=True)
                    console.success(f'container image [bold red]{t}[/] deleted successfully')
                    deleted = True

    if deleted is False:
        console.error(f'No agent matching [bold white]{agent}[/] was found')
