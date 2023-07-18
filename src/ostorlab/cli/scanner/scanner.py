"""Scanner module that run scanner command in daemon mode."""
import asyncio
import logging
import sys
import socket

import click

from ostorlab.cli import console as cli_console
from ostorlab.cli.rootcli import rootcli
from ostorlab.scanner import start
from ostorlab.utils import scanner_state_reporter
from ostorlab.utils import ip

console = cli_console.Console()

logger = logging.getLogger(__name__)

WAIT_CAPTURE_INTERVAL = 300


async def _start_periodic_persist_state(
    scanner_id: int, scan_id: int | None, errors: str | None
):
    while True:
        state_report = scanner_state_reporter.ScannerStateReporter(
            scanner_id=int(scanner_id),
            scan_id=scan_id,
            hostname=socket.gethostname(),
            ip=ip.get_public_ip(),
            errors=errors,
        )
        await state_report.report()
        logger.debug("Reporting the scanner state.")
        await asyncio.sleep(WAIT_CAPTURE_INTERVAL)


@rootcli.command()
@click.option("--scanner-id", help="The scanner identifier.", required=True)
@click.option("--daemon/--no-daemon", help="Run in daemon mode", default=True)
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

    # The import is done for Windows compatibility.
    import daemon as dm  # pylint: disable=import-outside-toplevel

    if daemon is True and ctx.obj.get("api_key") is not None:
        with dm.DaemonContext():
            loop = asyncio.get_event_loop()
            loop.create_task(
                _start_periodic_persist_state(
                    scanner_id=scanner_id,
                    scan_id=ctx.obj.get("scan_id"),
                    errors=ctx.obj.get("errors"),
                )
            )
            loop.run_until_complete(
                start.subscribe_to_nats(
                    api_key=ctx.obj["api_key"], scanner_id=scanner_id
                )
            )
            try:
                logger.info("starting forever loop")
                loop.run_forever()
            finally:
                logger.info("closing loop")
                loop.close()
    if daemon is False and ctx.obj.get("api_key") is not None:
        loop = asyncio.get_event_loop()
        loop.create_task(
            _start_periodic_persist_state(
                scanner_id=scanner_id,
                scan_id=ctx.obj.get("scan_id"),
                errors=ctx.obj.get("errors"),
            )
        )
        loop.run_until_complete(
            start.subscribe_to_nats(api_key=ctx.obj["api_key"], scanner_id=scanner_id)
        )
        try:
            logger.info("starting forever loop")
            loop.run_forever()
        finally:
            logger.info("closing loop")
            loop.close()
