"""Vulnz List command."""
import logging

import click

from ostorlab.cli import console as cli_console
from ostorlab.cli.vulnz import vulnz

console = cli_console.Console()

logger = logging.getLogger(__name__)


@vulnz.command(name='list')
@click.option('--scan-id', '-s', 'scan_id', help='Id of the scan.', required=True)
@click.pass_context
def list_cli(ctx: click.core.Context, scan_id: int) -> None:
    """CLI command to list vulnerabilities for a scan."""

    runtime_instance = ctx.obj['runtime']
    console.info(f'Fetching vulnerabilities for scan {scan_id}')
    runtime_instance.list_vulnz(scan_id=scan_id)
