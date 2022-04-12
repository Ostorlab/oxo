"""Asset of type file.
This module takes care of preparing a generic file of type before injecting it to the runtime instance."""
import io
import logging
from typing import List

import click

from ostorlab.assets import file as file_asset
from ostorlab.cli.scan.run import run

logger = logging.getLogger(__name__)


@run.run.command(name='file')
@click.argument('files', type=click.File(mode='rb'), nargs=-1, required=True)
@click.pass_context
def file_cli(ctx: click.core.Context, files: List[io.FileIO]) -> None:
    """Run scan for file asset."""
    runtime = ctx.obj['runtime']
    assets = []
    for f in files:
        assets.append(file_asset.File(content=f.read(), path=f.name))
    logger.debug('scanning assets %s', [str(asset) for asset in assets])
    runtime.scan(title=ctx.obj['title'], agent_group_definition=ctx.obj['agent_group_definition'], assets=assets)
