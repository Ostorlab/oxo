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
@click.option("--file", type=click.File(mode="rb"), multiple=False, required=True)
@click.option("--url", multiple=False, required=True)
@click.option("--schema-type", multiple=False, required=False)
@click.pass_context
def api_schema(
    ctx: click.core.Context,
    file: io.FileIO,
    url: str,
    schema_type: Optional[str] = None,
) -> None:
    """Run scan for an API Schema asset.

    Args:
        ctx: The Click context.
        file: The schema file.
        url: The URL that uses the schema.
        schema_type: Optional type of schema (GraphQL, WSDL, or OpenAPI).
    """
    runtime = ctx.obj["runtime"]
    assets = [
        api_schema_asset.ApiSchema(
            content=file.read(), url=url, schema_type=schema_type
        )
    ]

    logger.debug("scanning assets %s", [str(asset) for asset in assets])
    try:
        runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=assets,
        )
    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
