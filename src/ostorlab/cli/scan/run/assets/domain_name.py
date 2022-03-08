"""Asset of type Domain Name."""
import logging

import click

from ostorlab.assets import domain_name
from ostorlab.cli.scan.run import run

logger = logging.getLogger(__name__)


@run.run.command(name='domain-name')
@click.argument('name', required=True)
@click.pass_context
def domain_name_cli(ctx: click.core.Context, name: str) -> None:
    """Run scan for Domain Name asset."""
    runtime = ctx.obj['runtime']
    asset = domain_name.DomainName(name=name)
    logger.debug('scanning asset %s', asset)
    runtime.scan(title=ctx.obj['title'], agent_group_definition=ctx.obj['agent_group_definition'], asset=asset)
