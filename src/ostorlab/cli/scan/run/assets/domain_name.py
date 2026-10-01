"""Asset of type Domain Name."""

import logging

import click

from ostorlab import exceptions
from ostorlab.assets import domain_name
from ostorlab.cli.scan.run import run

logger = logging.getLogger(__name__)


@run.run.command(name="domain-name")
@click.argument("names", required=True, nargs=-1)
@click.pass_context
def domain_name_cli(ctx: click.core.Context, names: list[str]) -> None:
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
        raise click.ClickException(
            f"An error was encountered while running the scan: {e}"
        ) from e
