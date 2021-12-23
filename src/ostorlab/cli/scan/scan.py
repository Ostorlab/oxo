"""scan module that's handle running a scan for deferment."""
import io
import logging
import click
from ostorlab import assets
from ostorlab.cli.rootcli import scan

logger = logging.getLogger(__name__)


@scan.command()
@click.option('--file', type=click.File(), help='application .apk file.', required=True)
@click.pass_context
def android_apk(ctx: click.core.Context, file: io.FileIO) -> None:
    """run scan for android .apk package file.

     build an instance of asset class AndroidApk and pass it to the runtime.


    Args:
        file: path to the .apk file
        ctx: context object contains info from the command
    Returns:
        None:
    """

    runtime = ctx.obj['runtime']
    asset = assets.AndroidApk(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)


@scan.command()
@click.option('--file', type=click.File(), help='path for android .aab file.', required=True)
@click.pass_context
def android_aab(ctx: click.core.Context, file: io.FileIO) -> None:
    """run scan for android .aab package file.

     Build an instance of Asset class AndroidAab and pass it to the runtime.

    Args:
        file: path to the .apk file
        ctx: context object contains info from the command

    Returns:
        None:
    """
    runtime = ctx.obj['runtime']
    asset = assets.AndroidAab(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)


@scan.command()
@click.option('--file', type=click.File(), help='application .ipa file.', required=True)
@click.pass_context
def ios_ipa(ctx, file):
    """run scan for IOS .ipa package file.

     Build an instance of Asset class IOSIpa and pass it to the runtime

       Args:
           file: path to the .ipa file
           ctx: context object contains info from the command

       Returns:
           None:
       """

    runtime = ctx.obj['runtime']
    asset = assets.IOSIpa(file)
    runtime.scan(agent_run_definition=ctx.obj['agent_run_definition'], asset=asset)
