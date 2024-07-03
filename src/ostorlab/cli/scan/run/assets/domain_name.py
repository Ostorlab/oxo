"""Asset of type Domain Name."""

import logging
from typing import List

import click

from ostorlab.assets import domain_name
from ostorlab.cli.scan.run import run
from ostorlab import exceptions
from ostorlab.cli import console as cli_console

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="domain-name")
@click.argument("names", required=True, nargs=-1)
@click.pass_context
def domain_name_cli(ctx: click.core.Context, names: List[str]) -> None:
    """Run scan for Domain Name asset."""
    runtime = ctx.obj["runtime"]
    assets = []
    for d in names:
        assets.append(domain_name.DomainName(name=d))
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
