"""Asset of type Link."""
import logging

import click

from ostorlab.assets import link as link_asset
from ostorlab.cli.scan.run import run

logger = logging.getLogger(__name__)


@run.run.command()
@click.option('--url', help='Url to scan.', required=True)
@click.option('--method', help='HTTP method.', required=True)
@click.pass_context
def link(ctx: click.core.Context, url: str, method: str) -> None:
    """Run scan for link."""
    runtime = ctx.obj['runtime']
    asset = link_asset.Link(url=url, method=method)
    logger.debug('scanning asset %s', asset)
    runtime.scan(title=ctx.obj['title'], agent_group_definition=ctx.obj['agent_group_definition'], assets=[asset])
