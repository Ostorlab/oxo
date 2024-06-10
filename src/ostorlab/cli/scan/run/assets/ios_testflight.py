"""This module triggers a scan using the ios_testflight asset."""

import logging

import click

from ostorlab.cli.scan.run import run
from ostorlab.cli import console as cli_console
from ostorlab.assets import ios_testflight as ios_testflight_asset
from ostorlab import exceptions

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="ios-testflight")
@click.option("--application-url", required=False)
@click.pass_context
def ios_testflight(ctx: click.core.Context, application_url: str) -> None:
    """Run scan using testflight url."""
    runtime = ctx.obj["runtime"]
    assets = [ios_testflight_asset.IOSTestflight(application_url=application_url)]
    logger.debug("scanning assets %s", [str(asset) for asset in assets])
    try:
        runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=assets,
        )
    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
