"""Asset of type .IPA.
This module takes care of preparing a file of type .IPA before calling the create mobile scan API.
"""

import click
import io

from ostorlab.cli.ci_scan.run import run
from ostorlab.cli.ci_scan.run.assets import mobile
from ostorlab.apis import scan_create as scan_create_api


@run.run.command()
@click.argument('file', type=click.File(mode='rb'), required=True)
@click.pass_context
def ios_ipa(ctx: click.core.Context, file: io.FileIO):
    """Create scan for iOS .IPA package file."""
    mobile.run_mobile_scan(ctx, file, scan_create_api.MobileAssetType.IOS)
