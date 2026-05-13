"""Asset of type repository.
This module prepares a source code repository asset before injecting it to the runtime."""

import logging
from typing import Optional

import click

from ostorlab.assets import repository as repository_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run
from ostorlab import exceptions

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="repository")
@click.option("--origin-url", required=True)
@click.option("--commit-hash", required=True)
@click.pass_context
def repository_cli(
    ctx: click.core.Context,
    origin_url: Optional[str] = None,
    commit_hash: Optional[str] = None,
) -> None:
    """Run scan for a source code repository asset."""
    assets = [
        repository_asset.Repository(origin_url=origin_url, commit_hash=commit_hash)
    ]

    logger.debug("scanning assets %s", [str(a) for a in assets])
    runtime = ctx.obj["runtime"]
    try:
        runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=assets,
        )
    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
