"""Scanner module that run scanner command in daemon mode."""
import asyncio
import logging
import sys
import socket
from typing import Optional

import click

from ostorlab import configuration_manager as config_manager
from ostorlab.cli import console as cli_console
from ostorlab.cli.rootcli import rootcli
from ostorlab.scanner import scan_handler
from ostorlab.utils import scanner_state_reporter
from ostorlab.utils import ip

console = cli_console.Console()

logger = logging.getLogger(__name__)

WAIT_CAPTURE_INTERVAL = 300


async def _start_periodic_persist_state(
    state_reporter: scanner_state_reporter.ScannerStateReporter,
):
    while True:
        await state_reporter.report()
        logger.debug("Reporting the scanner state.")
        await asyncio.sleep(WAIT_CAPTURE_INTERVAL)


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
    Scanner communicates with NATs to receive start scan messages.\n
    """
    if sys.platform != "linux":
        console.error("ostorlab scanner sub-command is only supported on Unix systems.")
        raise click.exceptions.Exit(2)

    api_key = config_manager.ConfigurationManager().api_key or ctx.obj.get("api_key")

    # The import is done for Windows compatibility.
    import daemon as dm  # pylint: disable=import-outside-toplevel

    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id=scanner_id, hostname=socket.gethostname(), ip=ip.get_ip()
    )

    if daemon is True:
        with dm.DaemonContext():
            start_nats_subscription_asynchronously(api_key, scanner_id, state_reporter)
    else:
        start_nats_subscription_asynchronously(api_key, scanner_id, state_reporter)


def start_nats_subscription_asynchronously(
    api_key: Optional[str],
    scanner_id: str,
    state_reporter: scanner_state_reporter.ScannerStateReporter,
) -> None:
    """Run subscription to nats in eventloop.

    Args:
        api_key: The api key to login to the platform.
        scanner_id: The id of the scanner.
    """
    if api_key is None:
        logger.error("No api key provided.")
    loop = asyncio.get_event_loop()
    loop.create_task(_start_periodic_persist_state(state_reporter=state_reporter))
    loop.run_until_complete(
        scan_handler.subscribe_nats(
            api_key=api_key, scanner_id=scanner_id, state_reporter=state_reporter
        )
    )
    try:
        logger.debug("Closing loop.")
        loop.run_forever()
    finally:
        logger.debug("closing loop.")
        loop.close()
