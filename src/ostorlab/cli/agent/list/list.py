"""Agent List command."""
import io
import logging

import click
import docker

from ostorlab.agent.schema import loader
from ostorlab.agent.schema import validator
from ostorlab.cli import console as cli_console
from ostorlab.cli.agent import agent

console = cli_console.Console()

logger = logging.getLogger(__name__)


@agent.command()
def list() -> None:
    """CLI command to list installed agents."""
    docker_client = docker.from_env()
    images = docker_client.images.list()
    for im in images:
        print(im)
        print(im.id)
        print(im.attrs)
        print(im.labels)
        print(im.tags)
        print(im.history())