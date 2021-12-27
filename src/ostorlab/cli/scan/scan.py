"""Scan module that handles running a scan using a list of agent keys and a target asset."""
from typing import Optional

from ostorlab.cli.rootcli import rootcli
import click


@rootcli.group()
@click.option('--proxy', '-X', help='Proxy to route HTTPS requests through.')
@click.option('--tlsverify/--no-tlsverify', help='Control TLS server certificate verification.', default=True)
@click.pass_context
def scan(ctx: click.core.Context, proxy: Optional[str], tlsverify: bool) -> None:
    """You can use scan [subcommand] to list, start or stop a scan.\n
    Examples:\n
        - Show list of scans: ostorlab scan --list\n
        - Show full details of a scan: ostorlab scan describe --scan=scan_id.\n
    """
    ctx.obj['proxy'] = proxy
    ctx.obj['tlsverify'] = tlsverify
    pass
