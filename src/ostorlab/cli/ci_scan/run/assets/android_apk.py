"""Asset of type .APK package file.
This module takes care of preparing a file of type .APK before calling the create mobile scan API.
"""
import io
import click

from ostorlab.cli.ci_scan.run import run
from ostorlab.cli.ci_scan.run.assets import mobile
from ostorlab.apis import scan_create as scan_create_api


@run.run.command()
@click.argument('file', type=click.File(mode='rb'), required=True)
@click.pass_context
def android_apk(ctx: click.core.Context, file: io.FileIO) -> None:
    """Create scan for android .APK package file."""
    mobile.run_mobile_scan(ctx, file, scan_create_api.MobileAssetType.ANDROID)
