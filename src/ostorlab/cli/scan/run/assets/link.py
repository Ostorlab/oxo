"""Asset of type Link."""

import logging
from typing import List, Optional, Dict

import click

from ostorlab.assets import link as link_asset
from ostorlab.cli.scan.run import run
from ostorlab.cli import console as cli_console
from ostorlab import exceptions

logger = logging.getLogger(__name__)
console = cli_console.Console()


def _parse_key_value_arg(value: str) -> Dict[str, str]:
    """Parse a key-value pair, separated by '=' or ':'."""
    if "=" in value:
        key, val = value.split("=", 1)
        return {"name": key.strip(), "value": val.strip()}
    if ":" in value:
        key, val = value.split(":", 1)
        return {"name": key.strip(), "value": val.strip()}
    raise click.BadParameter(
        f'Invalid format for "{value}". Use key=value or key:value.'
    )


@run.run.command()
@click.option("--url", help="URL to scan.", required=True)
@click.option("--method", help="HTTP method.", required=True)
@click.option("--body", help="Request body.", required=False)
@click.option(
    "--header",
    "headers",
    help="Request header. Can be specified multiple times. Format is 'key:value' or 'key=value'.",
    required=False,
    multiple=True,
)
@click.option(
    "--cookie",
    "cookies",
    help="Request cookie. Can be specified multiple times. Format is 'key:value' or 'key=value'.",
    required=False,
    multiple=True,
)
@click.pass_context
def link(
    ctx: click.core.Context,
    url: str,
    method: str,
    body: Optional[str],
    headers: List[str],
    cookies: List[str],
) -> None:
    """Run scan for a link."""
    runtime = ctx.obj["runtime"]
    try:
        parsed_headers = [_parse_key_value_arg(h) for h in headers]
        parsed_cookies = [_parse_key_value_arg(c) for c in cookies]
    except click.BadParameter as e:
        console.error(e.message)
        raise click.exceptions.Exit(2) from e

    body = body.encode() if body is not None else None
    asset = link_asset.Link(
        url=url,
        method=method,
        body=body,
        extra_headers=parsed_headers,
        cookies=parsed_cookies,
    )
    logger.debug("scanning asset %s", asset)
    try:
        created_scan = runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=[asset],
        )
        if created_scan is not None:
            runtime.link_agent_group_scan(
                created_scan, ctx.obj["agent_group_definition"]
            )
            runtime.link_assets_scan(created_scan.id, [asset])

    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
