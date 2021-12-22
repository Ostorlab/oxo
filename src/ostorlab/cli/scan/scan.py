""" scan module thats handle running a scan for deferment asset  """
import io
import logging
import click
from ostorlab.assets import AndroidApk, IOSIpa, AndroidAab
from ostorlab.cli.rootcli import scan

logger = logging.getLogger(__name__)


@scan.command()
@click.option('--file', type=click.File(), help='application .apk file.', required=True)
@click.pass_context
def android_apk(ctx: click.core.Context, file: io.FileIO) -> None:
    """
    run scan for android .apk package file, Build an instance of Asset class and pass it to the runtime

    Args:
        file (io.File): path to the .apk file
        ctx (click.core.Context): context object contains info from the command
    Returns:
        None:
    """

    runtime = ctx.obj['runtime']
    asset = AndroidApk(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)


@scan.command()
@click.option('--file', type=click.File(), help='application .aab file.', required=True)
@click.pass_context
def android_aab(ctx: click.core.Context, file: io.FileIO) -> None:
    """
    run scan for android .aab package file, Build an instance of Asset class and pass it to the runtime

    Args:
        file (io.File): path to the .apk file
        ctx (click.core.Context): context object contains info from the command

    Returns:
        None:
    """
    runtime = ctx.obj['runtime']
    asset = AndroidAab(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)


@scan.command()
@click.option('--file', type=click.File(), help='application .ipa file.', required=True)
@click.pass_context
def ios_ipa(ctx, file):
    """
       run scan for ios .ipa package file, Build an instance of Asset class and pass it to the runtime

       Args:
           file (io.File): path to the .apk file
           ctx (click.core.Context): context object contains info from the command

       Returns:
           None:
       """

    runtime = ctx.obj['runtime']
    asset = IOSIpa(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)
