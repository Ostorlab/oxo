"""Asset of type .AAB package file.
This module takes care of preparing a file of type .aab before injecting it to the runtime instance."""
import io
import logging
from typing import List, Optional

import click

from ostorlab.assets import android_aab as android_aab_asset
from ostorlab.cli.scan.run import run
from ostorlab.cli import console as cli_console


console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command()
@click.option('files', type=click.File(mode='rb'), multiple=True, required=False)
@click.option('url', multiple=True, required=False)
@click.pass_context
def android_aab(ctx: click.core.Context,
                files: Optional[List[io.FileIO]] = None,
                url: Optional[List[str]] = None) -> None:
    """Run scan for android .AAB package file."""
    runtime = ctx.obj['runtime']
    assets = []
    if files != []:
        for f in files:
            assets.append(android_aab_asset.AndroidAab(content=f.read(), path=str(f.name)))
    elif url != []:
        for u in url:
            assets.append(android_aab_asset.AndroidAab(content_url=u))
    else:
        console.error('Command accepts either path or source url of the aab file.')
        raise click.exceptions.Exit(2)

    logger.debug('scanning assets %s', [str(asset) for asset in assets])
    runtime.scan(title=ctx.obj['title'], agent_group_definition=ctx.obj['agent_group_definition'], assets=assets)
