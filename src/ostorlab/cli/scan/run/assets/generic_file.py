"""Asset of type generic file.
This module prepares a generic file asset before injecting it to the runtime."""

import io
import logging

import click

from ostorlab.assets import generic_file as generic_file_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run
from ostorlab import exceptions

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="generic-file")
@click.option(
    "--file", "files", type=click.File(mode="rb"), multiple=True, required=False
)
@click.option("--url", "urls", required=False, multiple=True)
@click.pass_context
def generic_file_cli(
    ctx: click.core.Context,
    files: tuple[io.FileIO, ...] = (),
    urls: tuple[str, ...] = (),
) -> None:
    """Run scan for a generic file asset."""
    runtime = ctx.obj["runtime"]
    assets = []

    if urls != () and files != ():
        console.error("Command accepts either path or source url of the generic file.")
        raise click.exceptions.Exit(2)
    if urls == () and files == ():
        console.error(
            "Command missing either file path or source url of the generic file."
        )
        raise click.exceptions.Exit(2)

    if files != ():
        for f in files:
            assets.append(
                generic_file_asset.GenericFile(content=f.read(), path=str(f.name))
            )
    if urls != ():
        for u in urls:
            assets.append(generic_file_asset.GenericFile(content_url=u))

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
