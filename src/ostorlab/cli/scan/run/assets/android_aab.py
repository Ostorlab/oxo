"""Asset of type .AAB package file.
This module takes care of preparing a file of type .aab before injecting it to the runtime instance."""

import io
import logging
from typing import Tuple, Optional

import click

from ostorlab.assets import android_aab as android_aab_asset
from ostorlab.cli.scan.run import run
from ostorlab.cli import console as cli_console


console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command()
@click.option("--file", type=click.File(mode="rb"), multiple=True, required=False)
@click.option("--url", multiple=True, required=False)
@click.pass_context
def android_aab(
    ctx: click.core.Context,
    file: Optional[Tuple[io.FileIO]] = (),
    url: Optional[Tuple[str]] = (),
) -> None:
    """Run scan for android .AAB package file."""
    runtime = ctx.obj["runtime"]
    assets = []

    if url != () and file != ():
        console.error("Command accepts either path or source url of the aab file.")
        raise click.exceptions.Exit(2)
    if url == () and file == ():
        console.error("Command missing either file path or source url of the aab file.")
        raise click.exceptions.Exit(2)

    if file != ():
        for f in file:
            assets.append(
                android_aab_asset.AndroidAab(content=f.read(), path=str(f.name))
            )
    if url != ():
        for u in url:
            assets.append(android_aab_asset.AndroidAab(content_url=u))

    logger.debug("scanning assets %s", [str(asset) for asset in assets])
    runtime.scan(
        title=ctx.obj["title"],
        agent_group_definition=ctx.obj["agent_group_definition"],
        assets=assets,
    )
