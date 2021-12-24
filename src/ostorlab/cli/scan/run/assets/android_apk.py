"""Asset of type .APK package file.
This module take care of preparing a file of type .APK before injecting it to the runtime instance.
"""
import io
import click
from ostorlab import assets
from ostorlab.cli.scan.run.run import run


@run.command()
@click.option('--file', type=click.File(), help='Application .APK file.', required=True)
@click.pass_context
def android_apk(ctx: click.core.Context, file: io.FileIO) -> None:
    """Run scan for android .APK package file."""

    runtime = ctx.obj['runtime']
    asset = assets.AndroidApk(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)
