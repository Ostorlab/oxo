"""This module is the entry point for ostorlab CLI."""
import click
from typing import Optional


@click.group()
@click.option('--proxy', '-X', help='Proxy to route HTTPS requests through.')
@click.option('--tlsverify/--no-tlsverify', help='Control tlsverify server verification.', default=True)
@click.pass_context
def rootcli(ctx: click.core.Context, proxy: Optional[str], tlsverify: bool) -> None:
    """Ostorlab is an open-source project to help automate security testing.\n
    Ostorlab standardizes interoperability between tools in a consistent, scalable, and performant way."""

    ctx.obj = {
        'proxy': proxy,
        'tlsverify': tlsverify
    }


@rootcli.group()
def agent():
    raise click.ClickException('NotImplementedError')


@rootcli.group()
def agentgroup():
    raise click.ClickException('NotImplementedError')


@rootcli.group()
def auth():
    """Creates a group for the auth command and attaches subcommands."""
    pass
