"""Asset of type agent for meta-scanning."""

import logging
from typing import Optional

import click

from ostorlab.assets import agent as agent_asset
from ostorlab.cli.scan.run import run
from ostorlab import exceptions
from ostorlab.cli import console as cli_console

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command()
@click.option("--key", help="Agent key.", required=True)
@click.option("--version", help="Agent version.", required=False)
@click.option("--git-location", help="Agent source Git repo.", required=False)
@click.option("--docker-location", help="Agent store docker URL.", required=False)
@click.option(
    "--yaml-file-location",
    help="Agent YAML definition path in the Git repo.",
    required=False,
)
@click.pass_context
def agent(
    ctx: click.core.Context,
    key: str,
    version: Optional[str] = None,
    git_location: Optional[str] = None,
    docker_location: Optional[str] = None,
    yaml_file_location: Optional[str] = None,
) -> None:
    """Run scan for agent."""
    runtime = ctx.obj["runtime"]
    asset = agent_asset.Agent(
        key=key,
        version=version,
        git_location=git_location,
        docker_location=docker_location,
        yaml_file_location=yaml_file_location,
    )
    logger.debug("scanning asset %s", asset)
    try:
        runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=[asset],
        )
    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
