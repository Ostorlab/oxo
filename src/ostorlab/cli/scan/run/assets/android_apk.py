"""Asset of type .APK package file.
This module takes care of preparing a file of type .APK before injecting it to the runtime instance.
"""
import io
import logging

import click

from ostorlab.assets import android_apk as android_apk_asset
from ostorlab.cli.scan.run import run

logger = logging.getLogger(__name__)


@run.run.command()
@click.option('--file', type=click.File(mode='rb'), help='Path to .APK file.', required=True)
@click.pass_context
def android_apk(ctx: click.core.Context, file: io.FileIO) -> None:
    """Run scan for android .APK package file."""
    runtime = ctx.obj['runtime']
    asset = android_apk_asset.AndroidApk(content=file.read(), path=file.name)
    logger.debug('scanning asset %s', asset)
    runtime.scan(title=ctx.obj['title'], agent_group_definition=ctx.obj['agent_group_definition'], asset=asset)
