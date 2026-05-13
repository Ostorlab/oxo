"""Asset of type repository.
This module takes care of preparing a source code repository asset before injecting it to the runtime instance."""

import io
import logging
from typing import Optional, Tuple

import click

from ostorlab.assets import repository as repository_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run
from ostorlab import exceptions

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="repository")
@click.option("--file", type=click.File(mode="rb"), multiple=True, required=False)
@click.option("--url", required=False, multiple=True)
@click.option("--repo-url", required=False)
@click.option("--commit-hash", required=False)
@click.pass_context
def repository_cli(
    ctx: click.core.Context,
    file: Optional[Tuple[io.FileIO]] = None,
    url: Optional[Tuple[str]] = None,
    repo_url: Optional[str] = None,
    commit_hash: Optional[str] = None,
) -> None:
    """Run scan for a source code repository asset."""
    assets = []
    if len(file) > 0:
        for f in file:
            assets.append(
                repository_asset.Repository(origin_url=repo_url, commit_hash=commit_hash)
            )
    elif len(url) > 0:
        for u in url:
            assets.append(
                repository_asset.Repository(origin_url=repo_url, commit_hash=commit_hash)
            )
    else:
        console.error("Command accepts either --file or --url.")
        raise click.exceptions.Exit(2)

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
