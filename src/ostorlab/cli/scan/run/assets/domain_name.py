"""Asset of type Domain Name."""

import logging
from typing import List

import click

from ostorlab.assets import domain_name
from ostorlab.cli.scan.run import run

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
    runtime.scan(
        title=ctx.obj["title"],
        agent_group_definition=ctx.obj["agent_group_definition"],
        assets=assets,
    )
