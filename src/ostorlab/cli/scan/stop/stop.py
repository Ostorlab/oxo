"""Module for the command list inside the group scan.
This module takes care of listing all the remote or local scans.
Example of usage:
    - ostorlab scan list --source=source."""

import click
from ostorlab.cli.scan import scan
from ostorlab.cli import console as cli_console

console = cli_console.Console()


@scan.command()
@click.argument("scan_id", required=True)
@click.pass_context
def stop(ctx: click.core.Context, scan_id: int) -> None:
    """Stop a scan.\n
    Usage:\n
        - ostorlab scan --runtime=local stop --id=id
    """

    runtime_instance = ctx.obj["runtime"]
    with console.status("Stopping scan"):
        runtime_instance.stop(scan_id=scan_id)
