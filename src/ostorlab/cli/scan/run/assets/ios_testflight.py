"""This module triggers a scan using the ios_testflight asset."""

import logging

import click

from ostorlab import exceptions
from ostorlab.assets import ios_testflight as ios_testflight_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="ios-testflight")
@click.option("--application-url", required=False)
@click.option("--app-name", required=False)
@click.pass_context
def ios_testflight(
    ctx: click.core.Context,
    application_url: str | None = None,
    app_name: str | None = None,
) -> None:
    """Run scan using a testflight url or the name of a testflight app."""
    if application_url is None and app_name is None:
        console.error("Command missing a testflight application url or app name.")
        raise click.exceptions.Exit(2)

    runtime = ctx.obj["runtime"]
    assets = [
        ios_testflight_asset.IOSTestflight(
            application_url=application_url, app_name=app_name
        )
    ]
    logger.debug("scanning assets %s", [str(asset) for asset in assets])
    try:
        runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=assets,
        )
    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
