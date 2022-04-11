"""Asset of type .AAB package file.
This module takes care of preparing a file of type .aab before injecting it to the runtime instance."""
import io
import logging
from typing import List

import click

from ostorlab.assets import android_aab as android_aab_asset
from ostorlab.cli.scan.run import run

logger = logging.getLogger(__name__)


@run.run.command()
@click.argument('files', type=click.File(mode='rb'), nargs=-1)
@click.option('--file', type=click.File(mode='rb'), help='Path to .AAB file.', required=False, multiple=True)
@click.pass_context
def android_aab(ctx: click.core.Context, file: List[io.FileIO], files: List[io.FileIO]) -> None:
    """Run scan for android .AAB package file."""
    runtime = ctx.obj['runtime']
    assets = []
    if len(files) > 0:
        for file in files:
            assets.append(android_aab_asset.AndroidAab(content=file.read(), path=file.name))
    else:
        assets.append(android_aab_asset.AndroidAab(content=file.read(), path=file.name))
    # asset = android_aab_asset.AndroidAab(content=file.read(), path=file.name)
    # logger.debug('scanning asset %s', asset)
    # runtime.scan(title=ctx.obj['title'], agent_group_definition=ctx.obj['agent_group_definition'], asset=asset)
