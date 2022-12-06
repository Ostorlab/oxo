"""Module for the command list inside the group scan.
This module takes care of listing all the remote or local scans.
Example of usage:
    - ostorlab scan list --source=source."""

import click

from ostorlab.cli import console as cli_console
from ostorlab.cli.scan import scan
from ostorlab.utils import styles

console = cli_console.Console()


@scan.command(name="list")
@click.option(
    "--page", "-p", help="Page number of scans you would like to see.", default=1
)
@click.option("--elements", "-e", help="Number of scans to show per page.", default=10)
@click.pass_context
def list_scans(ctx: click.core.Context, page: int, elements: int) -> None:
    """List all your scans.\n
    Usage:\n
        - ostorlab scan --runtime=runtime list
    """
    runtime_instance = ctx.obj["runtime"]
    with console.status("Fetching scans"):
        scans = runtime_instance.list(page=page, number_elements=elements)
        if scans is not None:
            console.success("Scans listed successfully.")
            columns = {
                "Id": "id",
                "Asset": "asset",
                "Created Time": "created_time",
                "Progress": "progress",
            }
            title = f"Showing {len(scans)} Scans"

            data = [
                {
                    "id": str(s.id),
                    "asset": s.asset,
                    "created_time": str(s.created_time),
                    "progress": styles.style_progress(s.progress),
                }
                for s in scans
            ]

            console.table(columns=columns, data=data, title=title)
        else:
            console.error("Error fetching scan list.")
