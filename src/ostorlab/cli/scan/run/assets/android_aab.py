"""Asset of type .AAB package file.
This module take care of preparing a file of type .aab before injecting it to the runtime instance."""
import io
import click
from ostorlab import assets
from ostorlab.cli.scan.run import run


@run.command()
@click.option('--file', type=click.File(), help='Path for android .AAB file.', required=True)
@click.pass_context
def android_aab(ctx: click.core.Context, file: io.FileIO) -> None:
    """Run scan for android .AAB package file."""
    runtime = ctx.obj['runtime']
    asset = assets.AndroidAab(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)
