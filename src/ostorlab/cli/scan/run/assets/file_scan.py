"""Asset of type file."""
import io
import click
from ostorlab.assets import file_asset as Fileasset
from ostorlab.cli.scan.run import run


@run.run.command()
@click.option('--file', type=click.File(), help='Path to the file to be scanned.', required=True)
@click.pass_context
def file_scan(ctx: click.core.Context, file: io.FileIO) -> None:
    """Run scan for a file."""

    runtime = ctx.obj['runtime']
    asset = Fileasset.FileAsset(file.read())
    runtime.scan(agent_group_definition=ctx.obj['agent_group_definition'], asset=asset)
