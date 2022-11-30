"""This module takes care of download ipa using a bundle_id before injecting it to the runtime instance."""
import logging
from typing import Tuple, Optional

import click

from ostorlab.cli.scan.run import run
from ostorlab.cli import console as cli_console
from ostorlab.assets import ios_store

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name='ios_store')
@click.option('--bundle-id', multiple=True, required=False)
@click.pass_context
def android_store(ctx: click.core.Context,
                  bundle_id: Optional[Tuple[str]] = ()) -> None:
    """Run download from store scan for ios bundle id."""
    runtime = ctx.obj['runtime']
    assets = []
    if bundle_id != ():
        for bundle in bundle_id:
            assets.append(ios_store.IOSStore(bundle_id=bundle))
    else:
        console.error('Command missing package name.')
        raise click.exceptions.Exit(2)

    logger.debug('scanning assets %s', [str(asset) for asset in assets])
    runtime.scan(title=ctx.obj['title'], agent_group_definition=ctx.obj['agent_group_definition'], assets=assets)
