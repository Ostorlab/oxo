"""Asset of type Autonomous System Number."""

import logging
from collections.abc import Sequence

import click

from ostorlab import exceptions
from ostorlab.assets import asn as asn_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="asn")
@click.argument("asns", required=True, nargs=-1)
@click.pass_context
def asn_cli(ctx: click.core.Context, asns: Sequence[str]) -> None:
    """Run scan for Autonomous System Number asset."""
    runtime = ctx.obj["runtime"]
    assets = []
    for a in asns:
        assets.append(asn_asset.ASN(asn=a))
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
    except NotImplementedError:
        # The cloud runtime creates its assets through an API that has no ASN input yet.
        console.error("ASN scans are not supported on this runtime yet.")
