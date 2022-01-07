"""This module is the entry point for ostorlab CLI."""
from typing import Optional

import click


@click.group()
@click.pass_context
@click.option('--proxy', '-X', help='Proxy to route HTTPS requests through.')
@click.option('--tlsverify/--no-tlsverify', help='Control TLS server certificate verification.', default=True)
def rootcli(ctx: click.core.Context, proxy: Optional[str] = None, tlsverify: Optional[bool] = True) -> None:
    """Ostorlab is an open-source project to help automate security testing.\n
    Ostorlab standardizes interoperability between tools in a consistent, scalable, and performant way."""
    ctx.obj = {}
    ctx.obj['proxy'] = proxy
    ctx.obj['tlsverify'] = tlsverify
