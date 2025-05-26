"""Module for the command list inside the group scan.
This module takes care of listing all the remote or local scans.
Example of usage:
    - ostorlab scan list --source=source."""

from typing import Tuple

import click
from ostorlab.cli.scan import scan
from ostorlab.cli import console as cli_console

console = cli_console.Console()


@scan.command()
@click.argument("scan_ids", nargs=-1, type=int, required=False)
@click.option(
    "--all",
    "-a",
    "stop_all",
    is_flag=True,
    help="Stop all running scans",
    default=False,
)
@click.pass_context
def stop(ctx: click.core.Context, scan_ids: Tuple[int, ...], stop_all: bool) -> None:
    """Stop one or multiple scans.\n
    Usage:\n
        - ostorlab scan --runtime=local stop 4
        - ostorlab scan --runtime=local stop 4 5 6
        - ostorlab scan --runtime=local stop --all
    """
    if len(scan_ids) == 0 and stop_all is False:
        raise click.UsageError("Either provide scan IDs or use --all flag")

    runtime_instance = ctx.obj["runtime"]
    if stop_all is True:
        scans_list = runtime_instance.list()
        ids_to_stop = [
            s.id
            for s in scans_list
            if s.progress == "in_progress" or s.progress == "not_started"
        ]
        if len(ids_to_stop) == 0:
            console.warning("No running scans found.")
            return
    else:
        ids_to_stop = list(scan_ids)

    console.info(f"Stopping {len(ids_to_stop)} scan(s).")
    for scan_id in ids_to_stop:
        runtime_instance.stop(scan_id=scan_id)
