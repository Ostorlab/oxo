"""Asset of type file.
This module takes care of preparing a generic file of type before injecting it to the runtime instance."""

import io
import logging
from typing import Optional, Tuple

import click

from ostorlab.assets import file as file_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run
from ostorlab import exceptions

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="file")
@click.option("--file", type=click.File(mode="rb"), multiple=True, required=False)
@click.option("--url", multiple=True, required=False)
@click.pass_context
def file_cli(
    ctx: click.core.Context,
    file: Optional[Tuple[io.FileIO]] = None,
    url: Optional[Tuple[str]] = None,
) -> None:
    """Run scan for file asset."""
    runtime = ctx.obj["runtime"]
    assets = []
    if len(file) > 0:
        for f in file:
            assets.append(file_asset.File(content=f.read(), path=str(f.name)))
    elif len(url) > 0:
        for u in url:
            assets.append(file_asset.File(content_url=u))
    else:
        console.error("Command accepts either path or source url of the file.")
        raise click.exceptions.Exit(2)

    logger.debug("scanning assets %s", [str(asset) for asset in assets])
    try:
        runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=assets,
        )
    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
