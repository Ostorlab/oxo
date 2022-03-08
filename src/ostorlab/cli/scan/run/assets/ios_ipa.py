"""Asset of type .IPA (IOS App Store Package).
This module takes care of preparing a file of type .IPA before injecting it to the runtime instance.
"""

import logging

import click

from ostorlab.assets import ios_ipa as ios_ipa_asset
from ostorlab.cli.scan.run import run

logger = logging.getLogger(__name__)


@run.run.command()
@click.option('--file', type=click.File(mode='rb'), help='Path to .IPA file.', required=True)
@click.pass_context
def ios_ipa(ctx, file):
    """Run scan for .IPA package file."""
    runtime = ctx.obj['runtime']
    asset = ios_ipa_asset.IOSIpa(content=file.read(), path=file.name)
    logger.debug('scanning asset %s', asset)
    runtime.scan(title=ctx.obj['title'], agent_group_definition=ctx.obj['agent_group_definition'], asset=asset)
