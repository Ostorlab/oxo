"""Asset of type Link."""

import logging
from typing import List

import click

from ostorlab.assets import link as link_asset
from ostorlab.cli.scan.run import run
from ostorlab.cli import console as cli_console
from ostorlab import exceptions

logger = logging.getLogger(__name__)
console = cli_console.Console()


@run.run.command()
@click.option("--url", help="List of Urls to scan.", required=True, multiple=True)
@click.option("--method", help="List of HTTP methods.", required=True, multiple=True)
@click.pass_context
def link(ctx: click.core.Context, url: List[str], method: List[str]) -> None:
    """Run scan for links."""
    runtime = ctx.obj["runtime"]
    if len(url) != len(method):
        console.error("Make sure every URL has its corresponding method.")
        raise click.exceptions.Exit(2)
    assets = []
    for u, m in zip(url, method):
        asset = link_asset.Link(url=u, method=m)
        assets.append(asset)
    logger.debug("scanning assets %s", asset)
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
