"""Scanner module that run scanner command in daemon mode."""
import asyncio
import logging
import sys
from typing import Optional

import click

from ostorlab import configuration_manager as config_manager
from ostorlab.cli import console as cli_console
from ostorlab.cli.rootcli import rootcli
from ostorlab.scanner import start

console = cli_console.Console()

logger = logging.getLogger(__name__)


@rootcli.command()
@click.option("--scanner-id", help="The scanner identifier.", required=True)
@click.option("--daemon/--no-daemon", help="Run in daemon mode.", default=True)
@click.pass_context
def scanner(
    ctx: click.core.Context,
    daemon: bool,
    scanner_id: str,
) -> None:
    """Ostorlab scanner enables running custom instances of scanners.
    Scanners communicates with NATs to receive start scan messages.\n
    """
    if sys.platform != "linux":
        console.error("ostorlab scanner sub-command is only supported on Unix systems.")
        raise click.exceptions.Exit(2)

    api_key = config_manager.ConfigurationManager().api_key or ctx.obj.get("api_key")

    # The import is done for Windows compatibility.
    import daemon as dm  # pylint: disable=import-outside-toplevel

    if daemon is True:
        with dm.DaemonContext():
            start_nats_subscription_asynchronously(api_key, scanner_id)
    else:
        start_nats_subscription_asynchronously(api_key, scanner_id)


def start_nats_subscription_asynchronously(
    api_key: Optional[str], scanner_id: str
) -> None:
    """Run subscription to nats in eventloop.

    Args:
        api_key: The api key to login to the platform.
        scanner_id: The id of the scanner.
    """
    if api_key is None:
        logger.error("No api key provided.")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        start.subscribe_to_nats(api_key=api_key, scanner_id=scanner_id)
    )
    try:
        logger.info("starting forever loop")
        loop.run_forever()
    finally:
        logger.info("closing loop")
        loop.close()
