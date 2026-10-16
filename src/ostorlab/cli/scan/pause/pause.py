"""Module for the command pause inside the group scan.
This module takes care of pausing a running local scan.
Example of usage:
    - oxo scan pause 4"""

import click

from ostorlab.cli import console as cli_console
from ostorlab.cli.scan.scan import scan
from ostorlab.runtimes.local import runtime as local_runtime

console = cli_console.Console()


@scan.command()
@click.argument("scan_id", type=int, required=True)
@click.pass_context
def pause(ctx: click.core.Context, scan_id: int) -> None:
    """Pause a running scan, resume it later with `oxo scan resume`.\n
    Usage:\n
        - oxo scan --runtime=local pause 4
    """
    runtime_instance = ctx.obj["runtime"]
    if isinstance(runtime_instance, local_runtime.LocalRuntime) is False:
        raise click.ClickException(
            "Pausing a scan is only supported by the local runtime."
        )
    try:
        runtime_instance.pause(scan_id=scan_id)
    except local_runtime.ScanPauseError as e:
        console.error(f"Could not pause scan {scan_id}: {e}")
        raise click.exceptions.Exit(1) from e
