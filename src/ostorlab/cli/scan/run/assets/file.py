"""Asset of type file.
This module takes care of preparing a generic file of type before injecting it to the runtime instance."""
import io
import click
from ostorlab.assets import file as file_asset
from ostorlab.cli.scan.run import run


@run.run.command(name='file')
@click.option('--file', type=click.File(mode='rb'), help='Path to file.', required=True)
@click.pass_context
def file_cli(ctx: click.core.Context, file: io.FileIO) -> None:
    """Run scan for file asset."""
    runtime = ctx.obj['runtime']
    asset = file_asset.File(file.read())
    runtime.scan(agent_group_definition=ctx.obj['agent_group_definition'], asset=asset)
