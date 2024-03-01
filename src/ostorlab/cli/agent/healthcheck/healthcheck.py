"""Agent Healthcheck commands."""

import logging

import click
import httpx

from ostorlab.cli import console as cli_console
from ostorlab.cli.agent import agent

console = cli_console.Console()

logger = logging.getLogger(__name__)


@agent.command()
@click.option(
    "--host",
    "-h",
    help="Host to check healthy agent.",
    required=False,
    default="localhost",
)
@click.option(
    "--port",
    "-p",
    help="Port to check healthy agent.",
    required=False,
    default=5000,
    type=int,
)
@click.option("--https/--no-https", help="Enable HTTPS.", required=False, default=False)
def healthcheck(host: str, port: int, https: bool = False) -> None:
    """Minimal agent healthcheck command to ensure the agent response with 200 OK on localhost:5000 by default."""
    if https:
        url = f"https://{host}:{port}/status"
    else:
        url = f"http://{host}:{port}/status"

    try:
        response = httpx.get(url, timeout=10)
        if response.status_code != 200:
            console.error(f"Response status code is {response.status_code}")
            raise click.exceptions.Exit(2)
        else:
            console.success(f"Healthcheck OK on {url}!")
    except httpx.HTTPError as e:
        console.error(f"Error checking agent health on {url}")
        raise click.exceptions.Exit(2) from e
