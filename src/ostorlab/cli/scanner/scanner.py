""""""
import asyncio
import logging

import click
import daemon as dm

from ostorlab.cli import console as cli_console
from ostorlab.cli.scanner import start
from ostorlab.cli.scan import scan

console = cli_console.Console()

logger = logging.getLogger(__name__)


@scan.group()
@click.option("--daemon/--no-daemon", help="Run in daemon mode", default=True)
@click.option("--scanner-id", help="The scanner identifier.", required=True)
@click.pass_context
def run(
    ctx: click.core.Context,
    daemon: bool,
    scanner_id: str,
) -> None:
    """Start a new scan on a specific asset.\n
    Example:\n
        - ostorlab scan run --agent=agent/ostorlab/nmap --agent=agent/google/tsunami --title=test_scan ip 8.8.8.8
    """
    if daemon is True and scanner_id is not None and ctx.invoked_subcommand is not None:
        with dm.DaemonContext():
            asyncio.get_event_loop().run_until_complete(start.subscribe_to_nats(api_key=ctx.obj["api_key"], scanner_id=scanner_id))