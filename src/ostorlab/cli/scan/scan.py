import logging
import click

from ostorlab.assets import AndroidApk, IOSIpa, AndroidAab

from ostorlab.cli.rootcli import scan

logger = logging.getLogger(__name__)


@scan.command()
@click.option('--file', type=click.File(), help='application .apk file.', required=True)
@click.pass_context
def android_apk(ctx, file):
    runtime = ctx.obj['runtime']
    asset = AndroidApk(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)


@scan.command()
@click.option('--file', type=click.File(), help='application .aab file.', required=True)
@click.pass_context
def android_aab(ctx, file):
    runtime = ctx.obj['runtime']
    asset = AndroidAab(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)


@scan.command()
@click.option('--file', type=click.File(), help='application .ipa file.', required=True)
@click.pass_context
def ios_ipa(ctx, file):
    runtime = ctx.obj['runtime']
    asset = IOSIpa(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)
