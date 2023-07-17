"""Scanner module that run scanner command in daemon mode."""
import sys
import asyncio
import logging

import click


from ostorlab.cli import console as cli_console
from ostorlab.scanner import start
from ostorlab.cli.rootcli import rootcli

console = cli_console.Console()

logger = logging.getLogger(__name__)


@rootcli.command()
@click.option("--scanner-id", help="The scanner identifier.", required=True)
@click.pass_context
def scanner(
    ctx: click.core.Context,
    scanner_id: str,
) -> None:
    """Ostorlab scanner enables running custom instances of scanners.
    Scanners communicates with NATs to receive start scan messages.\n
    """
    if sys.platform != "linux":
        console.error("ostorlab scanner sub-command is only supported on Unix systems.")
        raise click.exceptions.Exit(2)

    # The import is done for Windows compatibility.
    import daemon as dm  # pylint: disable=import-outside-toplevel

    with dm.DaemonContext():
        asyncio.get_event_loop().run_until_complete(
            start.subscribe_to_nats(api_key=ctx.obj["api_key"], scanner_id=scanner_id)
        )
