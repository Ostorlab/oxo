"""Asset of type .IPA (IOS App Store Package).
This module takes care of preparing a file of type .IPA before injecting it to the runtime instance.
"""
import io
import logging
from typing import List

import click

from ostorlab.assets import ios_ipa as ios_ipa_asset
from ostorlab.cli.scan.run import run

logger = logging.getLogger(__name__)


@run.run.command()
@click.argument('files', type=click.File(mode='rb'), nargs=-1, required=True)
@click.pass_context
def ios_ipa(ctx: click.core.Context, files: List[io.FileIO]) -> None:
    """Run scan for .IPA package file."""
    runtime = ctx.obj['runtime']
    assets = []
    for f in files:
        assets.append(ios_ipa_asset.IOSIpa(content=f.read(), path=f.name))
    logger.debug('scanning assets %s', [str(asset) for asset in assets])
    runtime.scan(title=ctx.obj['title'], agent_group_definition=ctx.obj['agent_group_definition'], assets=assets)
