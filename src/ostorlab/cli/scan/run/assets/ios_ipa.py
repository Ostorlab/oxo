"""Asset of type .IPA (IOS App Store Package).
This module takes care of preparing a file of type .IPA before injecting it to the runtime instance.
"""

import io
import logging
import pathlib
from typing import Tuple, Optional

import click

from ostorlab.assets import ios_ipa as ios_ipa_asset
from ostorlab.cli.scan.run import run
from ostorlab.cli import console as cli_console
from ostorlab import exceptions
from ostorlab.cli.scan.run.assets import common

console = cli_console.Console()
logger = logging.getLogger(__name__)

OSTORLAB_PRIVATE_DIR = pathlib.Path.home() / ".ostorlab"
UPLOADS_DIR = OSTORLAB_PRIVATE_DIR / "uploads"


@run.run.command()
@click.option("--file", type=click.File(mode="rb"), multiple=True, required=False)
@click.option("--url", multiple=True, required=False)
@click.pass_context
def ios_ipa(
    ctx: click.core.Context,
    file: Optional[Tuple[io.FileIO]] = (),
    url: Optional[Tuple[str]] = (),
) -> None:
    """Run scan for .IPA package file."""
    runtime = ctx.obj["runtime"]
    assets = []

    if url != () and file != ():
        console.error("Command accepts either path or source url of the ipa file.")
        raise click.exceptions.Exit(2)
    if url == () and file == ():
        console.error("Command missing either file path or source url of the ipa file.")
        raise click.exceptions.Exit(2)

    if file != ():
        for f in file:
            assets.append(ios_ipa_asset.IOSIpa(content=f.read(), path=str(f.name)))
    if url != ():
        # Create the uploads directory if it doesn't exist
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        for u in url:
            # Generate a unique filename for the downloaded file
            file_name = f"{common.hash_url(u)}.ipa"
            save_path = UPLOADS_DIR / file_name
            console.info(f"Downloading file from {u} to {save_path}...")
            try:
                content = common.download_file(u, save_path)
            except exceptions.OstorlabError as e:
                console.error(str(e))
                raise click.exceptions.Exit(2)
            console.success(f"File downloaded successfully and saved to {save_path}")
            assets.append(
                ios_ipa_asset.IOSIpa(
                    content_url=u, path=str(save_path), content=content
                )
            )

    logger.debug("scanning assets %s", [str(asset) for asset in assets])
    try:
        created_scan = runtime.scan(
            title=ctx.obj["title"],
            agent_group_definition=ctx.obj["agent_group_definition"],
            assets=assets,
        )
        if created_scan is not None:
            runtime.link_agent_group_scan(
                created_scan, ctx.obj["agent_group_definition"]
            )
            runtime.link_assets_scan(created_scan.id, assets)

    except exceptions.OstorlabError as e:
        console.error(f"An error was encountered while running the scan: {e}")
