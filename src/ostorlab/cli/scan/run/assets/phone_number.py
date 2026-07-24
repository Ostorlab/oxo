"""Asset of type Phone Number."""

import logging

import click

from ostorlab import exceptions
from ostorlab.assets import phone_number
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="phone-number")
@click.argument("numbers", required=True, nargs=-1)
@click.pass_context
def phone_number_cli(ctx: click.core.Context, numbers: list[str]) -> None:
    """Run scan for Phone Number asset."""
    runtime = ctx.obj["runtime"]
    assets = []
    for n in numbers:
        assets.append(phone_number.PhoneNumber(number=n))
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
