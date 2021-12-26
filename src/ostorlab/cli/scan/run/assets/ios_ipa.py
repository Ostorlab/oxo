"""Asset of type .IPA (IOS App Store Package).
This module take care of preparing a file of type .IPA before injecting it to the runtime instance.
"""

import click
from ostorlab import assets
from ostorlab.cli.scan.run import run


@run.run.command()
@click.option('--file', type=click.File(), help='Path to .IPA file.', required=True)
@click.pass_context
def ios_ipa(ctx, file):
    """Run scan for .IPA package file."""

    runtime = ctx.obj['runtime']
    asset = assets.IOSIpa(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)
