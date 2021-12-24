"""Scan module that handles running a scan using a list of agent keys and a target asset.."""
import io
import logging
import click
from ostorlab import assets
from ostorlab.cli.rootcli import scan

logger = logging.getLogger(__name__)


@scan.command()
@click.option('--file', type=click.File(), help='Application .APK file.', required=True)
@click.pass_context
def android_apk(ctx: click.core.Context, file: io.FileIO) -> None:
    """Run scan for android .APK package file."""

    runtime = ctx.obj['runtime']
    asset = assets.AndroidApk(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)


@scan.command()
@click.option('--file', type=click.File(), help='Path for android .AAB file.', required=True)
@click.pass_context
def android_aab(ctx: click.core.Context, file: io.FileIO) -> None:
    """Run scan for android .AAB package file."""
    runtime = ctx.obj['runtime']
    asset = assets.AndroidAab(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)


@scan.command()
@click.option('--file', type=click.File(), help='Application .IPA file.', required=True)
@click.pass_context
def ios_ipa(ctx, file):
    """Run scan for IOS .IPA package file."""

    runtime = ctx.obj['runtime']
    asset = assets.IOSIpa(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)
