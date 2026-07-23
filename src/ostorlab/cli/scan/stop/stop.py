"""Module for the command list inside the group scan.
This module takes care of listing all the remote or local scans.
Example of usage:
    - ostorlab scan list --source=source."""

import click

from ostorlab.cli import console as cli_console
from ostorlab.cli.scan import scan

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
@click.option(
    "--last",
    "-l",
    "stop_last",
    is_flag=True,
    help="Stop the last created scan",
    default=False,
)
@click.pass_context
def stop(
    ctx: click.core.Context,
    scan_ids: tuple[int, ...],
    stop_all: bool,
    stop_last: bool,
) -> None:
    """Stop one or multiple scans.\n
    Usage:\n
        - ostorlab scan --runtime=local stop 4
        - ostorlab scan --runtime=local stop 4 5 6
        - ostorlab scan --runtime=local stop --all
        - ostorlab scan --runtime=local stop --last
    """
    if len(scan_ids) > 0 and (stop_all is True or stop_last is True):
        raise click.UsageError("Cannot provide scan IDs with --all or --last flags.")

    if stop_all is True and stop_last is True:
        raise click.UsageError("Cannot use --all and --last flags together.")

    if len(scan_ids) == 0 and stop_all is False and stop_last is False:
        raise click.UsageError("Either provide scan IDs or use --all or --last flag.")

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
    elif stop_last is True:
        scans_list = runtime_instance.list()
        if scans_list is None or len(scans_list) == 0:
            console.warning("No scans found.")
            return
        last_scan = max(scans_list, key=lambda s: s.created_time)
        ids_to_stop = [last_scan.id]
    else:
        ids_to_stop = list(scan_ids)

    console.info(f"Stopping {len(ids_to_stop)} scan(s).")
    for scan_id in ids_to_stop:
        runtime_instance.stop(scan_id=scan_id)
