"""This module is the entry point for ostorlab CLI."""
import logging
from typing import Optional

import click

logger = logging.getLogger('CLI')


@click.group()
@click.pass_context
@click.option('--api_key', help='API key to login to the platform.', required=False)
@click.option('--proxy', '-X', help='Proxy to route HTTPS requests through.')
@click.option('--tlsverify/--no-tlsverify', help='Control TLS server certificate verification.', default=True)
@click.option('-d', '--debug/--no-debug', help='Enable debug mode', default=False)
@click.option('-v', '--verbose/--no-verbose', help='Enable verbose mode', default=False)
def rootcli(ctx: click.core.Context, proxy: Optional[str] = None, tlsverify: Optional[bool] = True, debug: bool = False,
            verbose: bool = False, api_key: str = None) -> None:
    """Ostorlab is an open-source project to help automate security testing.\n
    Ostorlab standardizes interoperability between tools in a consistent, scalable, and performant way."""
    ctx.obj = {}
    ctx.obj['proxy'] = proxy
    ctx.obj['tlsverify'] = tlsverify
    ctx.obj['api_key'] = api_key
    if verbose is True:
        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        for l in loggers:
            l.setLevel(logging.INFO)
    if debug is True:
        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        for l in loggers:
            l.setLevel(logging.DEBUG)
