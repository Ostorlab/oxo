"""This module triggers a scan using the ios_store asset."""

import logging
from typing import Tuple, Optional

import click

from ostorlab.cli.scan.run import run
from ostorlab.cli import console as cli_console
from ostorlab.assets import ios_store as ios_store_asset
from ostorlab import exceptions

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="ios-store")
@click.option("--bundle-id", multiple=True, required=False)
@click.pass_context
def ios_store(ctx: click.core.Context, bundle_id: Optional[Tuple[str]] = ()) -> None:
    """Run scan for a bundle_id."""
    runtime = ctx.obj["runtime"]
    assets = []
    if bundle_id != ():
        for bundle in bundle_id:
            assets.append(ios_store_asset.IOSStore(bundle_id=bundle))
    else:
        console.error("Command missing a bundle id.")
        raise click.exceptions.Exit(2)

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
