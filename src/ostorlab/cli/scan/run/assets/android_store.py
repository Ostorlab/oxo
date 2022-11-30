"""This module takes care of download an apk using the package name before injecting it to the runtime instance."""
import logging
from typing import Tuple, Optional

import click

from ostorlab.cli.scan.run import run
from ostorlab.cli import console as cli_console
from ostorlab.assets import android_store

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name='android_store')
@click.option('--package-name', multiple=True, required=False)
@click.pass_context
def android_store(ctx: click.core.Context,
                  package_name: Optional[Tuple[str]] = ()) -> None:
    """Run download from store scan for android package name."""
    runtime = ctx.obj['runtime']
    assets = []
    if package_name != ():
        for package in package_name:
            assets.append(android_store.AndroidStore(package_name=package))
    else:
        console.error('Command missing package name.')
        raise click.exceptions.Exit(2)

    logger.debug('scanning assets %s', [str(asset) for asset in assets])
    runtime.scan(title=ctx.obj['title'], agent_group_definition=ctx.obj['agent_group_definition'], assets=assets)
