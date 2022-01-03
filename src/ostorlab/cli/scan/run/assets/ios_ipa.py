"""Asset of type .IPA (IOS App Store Package).
This module takes care of preparing a file of type .IPA before injecting it to the runtime instance.
"""

import click
from ostorlab.assets import ios_ipa as ios_ipa_asset
from ostorlab.cli.scan.run import run


@run.run.command()
@click.option('--file', type=click.File(), help='Path to .IPA file.', required=True)
@click.pass_context
def ios_ipa(ctx, file):
    """Run scan for .IPA package file."""

    runtime = ctx.obj['runtime']
    asset = ios_ipa_asset.IOSIpa(file.read())
    runtime.scan(agent_group_definition=ctx.obj['agent_run_definition'], asset=asset)
