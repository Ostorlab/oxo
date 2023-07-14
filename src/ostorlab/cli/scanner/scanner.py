""""""
import asyncio
import logging

import click
import daemon as dm

from ostorlab.cli import console as cli_console
from ostorlab.cli.scanner import start
from ostorlab.cli.rootcli import rootcli

console = cli_console.Console()

logger = logging.getLogger(__name__)


@rootcli.command()
@click.option("--daemon/--no-daemon", help="Run in daemon mode", default=True)
@click.option("--scanner-id", help="The scanner identifier.", required=True)
@click.pass_context
def scanner(
    ctx: click.core.Context,
    daemon: bool,
    scanner_id: str,
) -> None:
    """Invoke a scan in a daemon mode.\n
    Example:\n
        - ostorlab scanner --api-key [API_KEY] --daemon --scanner-id [SCANNER_ID]
    """
    if daemon is True and ctx.obj["api_key"] is not None:
        logger.info("Running scanner with daemon mode.")
        with dm.DaemonContext():
            asyncio.get_event_loop().run_until_complete(
                start.subscribe_to_nats(
                    api_key=ctx.obj["api_key"], scanner_id=scanner_id
                )
            )
    elif daemon is False and ctx.obj["api_key"] is not None:
        logger.info("Running scanner without daemon mode.")
        asyncio.get_event_loop().run_until_complete(
            start.subscribe_to_nats(api_key=ctx.obj["api_key"], scanner_id=scanner_id)
        )
