"""This module triggers a scan using the ApiSchema asset."""

import io
import logging
from typing import Optional

import click

from ostorlab.assets import api_schema as api_schema_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run
from ostorlab import exceptions

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="api-schema")
@click.option("--url", help="The URL to scan.", multiple=False, required=True)
@click.option(
    "--schema-file",
    type=click.File(mode="rb"),
    help="The file path of the schema.",
    multiple=False,
    required=False,
)
@click.option(
    "--schema-url",
    help="The URL from which to download the schema.",
    multiple=False,
    required=False,
)
@click.option(
    "--schema-type",
    help="The schema type (graphql, wsdl, or openapi).",
    multiple=False,
    required=False,
)
@click.pass_context
def api_schema(
    ctx: click.core.Context,
    url: str,
    schema_file: Optional[io.FileIO] = None,
    schema_url: Optional[str] = None,
    schema_type: Optional[str] = None,
) -> None:
    """Run scan for an API Schema asset.

    Args:
        ctx: The Click context.
        url: The URL to scan.
        schema_file: The file path of the schema.
        schema_url: The URL from which to download the schema.
        schema_type: Optional type of schema (graphql, wsdl, openapi).
    """
    if schema_file is None and schema_url is None:
        console.error("You must provide either --schema-file or --schema-url.")
        raise click.exceptions.Exit(2)
    runtime = ctx.obj["runtime"]
    assets = [
        api_schema_asset.ApiSchema(
            content=schema_file.read() if schema_file is not None else None,
            content_url=schema_url,
            endpoint_url=url,
            schema_type=schema_type,
        )
    ]

    logger.debug("Scanning assets %s", [str(asset) for asset in assets])
    try:
        runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=assets,
        )
    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
