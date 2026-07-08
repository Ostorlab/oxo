"""Asset of type repository archive.
This module prepares a source code repository archive asset before injecting it to the runtime."""

import io
import logging
from typing import Tuple, Optional

import click

from ostorlab.assets import repository_archive as repository_archive_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.run import run
from ostorlab import exceptions

console = cli_console.Console()
logger = logging.getLogger(__name__)


@run.run.command(name="repository-archive")
@click.option("--file", type=click.File(mode="rb"), multiple=True, required=False)
@click.option("--url", required=False, multiple=True)
@click.pass_context
def repository_archive_cli(
    ctx: click.core.Context,
    file: Optional[Tuple[io.FileIO]] = (),
    url: Optional[Tuple[str]] = (),
) -> None:
    """Run scan for a source code repository archive asset."""
    runtime = ctx.obj["runtime"]
    assets = []

    if url != () and file != ():
        console.error(
            "Command accepts either path or source url of the repository archive."
        )
        raise click.exceptions.Exit(2)
    if url == () and file == ():
        console.error(
            "Command missing either file path or source url of the repository archive."
        )
        raise click.exceptions.Exit(2)

    if file != ():
        for f in file:
            assets.append(
                repository_archive_asset.RepositoryArchive(
                    content=f.read(), path=str(f.name)
                )
            )
    if url != ():
        for u in url:
            assets.append(repository_archive_asset.RepositoryArchive(content_url=u))

    logger.debug("scanning assets %s", [str(asset) for asset in assets])
    try:
        runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=assets,
        )
    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
