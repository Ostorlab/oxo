"""Agent List command."""
import re
import logging
import click
import docker
from typing import Optional
from ostorlab.cli import console as cli_console
from ostorlab.cli.agent import agent

console = cli_console.Console()

logger = logging.getLogger(__name__)


@agent.command()
@click.option('--agent-key', '-a', help='Agent Key.', required=True)
@click.option('--agent-version-regex', '-r', help='Agent version matching regular expression.', required=False)
def delete(agent_key: str, agent_version_regex: Optional[str] = None) -> None:
    """CLI command to list installed agents."""
    docker_client = docker.from_env()
    images = docker_client.images.list()
    agent_container_name = agent_key.replace('/', '_')
    deleted = False
    for im in images:
        for t in im.tags:
            if t.split(':')[0] == agent_container_name:
                agent_container_version = t.split(':')[1]
                if agent_version_regex is None or re.match(agent_version_regex, agent_container_version):
                    console.info(f'deleting container container [bold red]{t}[/]')
                    docker_client.images.remove(t, force=True)
                    console.success(f'container image [bold red]{t}[/] deleted successfully')
                    deleted = True

    if deleted is False:
        console.error(f'No agent matching [bold white]{agent_key}[/] were found')
