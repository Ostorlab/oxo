"""Vulnz Describe command."""
import logging
from typing import Optional

import click

from ostorlab.cli import console as cli_console
from ostorlab.cli.vulnz import vulnz

console = cli_console.Console()

logger = logging.getLogger(__name__)


@vulnz.command(name='describe')
@click.option('--vuln-id', '-v', 'vuln_id', help='Id of the vulnerability.', required=False)
@click.option('--scan-id', '-s', 'scan_id', help='Id of the scan.', required=False)
@click.pass_context
def describe_cli(ctx, vuln_id: Optional[int] = None, scan_id: Optional[int] = None) -> None:
    """CLI command to describe a vulnerability."""
    runtime_instance = ctx.obj['runtime']
    with console.status(f'Fetching vulnerabilities for scan {scan_id}'):
        runtime_instance.describe_vuln(scan_id=scan_id, vuln_id=vuln_id)
