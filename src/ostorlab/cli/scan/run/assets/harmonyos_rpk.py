"""Asset of type .RPK package file.
This module takes care of preparing a file of type .RPK before injecting it to the runtime instance.
"""

import io
import logging
from typing import Tuple, Optional

import click

from ostorlab.assets import harmonyos_rpk as harmonyos_rpk_asset
from ostorlab.cli.scan.run import run
from ostorlab.cli import console as cli_console
from ostorlab import exceptions

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command()
@click.option("--file", type=click.File(mode="rb"), multiple=True, required=False)
@click.option("--url", required=False, multiple=True)
@click.pass_context
def harmonyos_rpk(
    ctx: click.core.Context,
    file: Optional[Tuple[io.FileIO]] = (),
    url: Optional[Tuple[str]] = (),
) -> None:
    """Run scan for HarmonyOS .RPK package file."""
    runtime = ctx.obj["runtime"]
    assets = []

    if url != () and file != ():
        console.error("Command accepts either path or source url of the rpk file.")
        raise click.exceptions.Exit(2)
    if url == () and file == ():
        console.error("Command missing either file path or source url of the rpk file.")
        raise click.exceptions.Exit(2)

    if file != ():
        for f in file:
            assets.append(
                harmonyos_rpk_asset.HarmonyOSRpk(content=f.read(), path=str(f.name))
            )
    if url != ():
        for u in url:
            assets.append(harmonyos_rpk_asset.HarmonyOSRpk(content_url=u))

    logger.debug("scanning assets %s", [str(asset) for asset in assets])
    try:
        created_scan = runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=assets,
        )
        if created_scan is not None:
            runtime.link_agent_group_scan(
                created_scan, ctx.obj["agent_group_definition"]
            )
            runtime.link_assets_scan(created_scan.id, assets)

    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
