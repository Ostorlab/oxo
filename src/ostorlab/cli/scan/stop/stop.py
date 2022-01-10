"""Module for the command list inside the group scan.
This module takes care of listing all the remote or local scans.
Example of usage:
    - ostorlab scan list --source=source."""

import click
from ostorlab.cli.scan import scan
from ostorlab.runtimes import local


@scan.command()
@click.option('--runtime', '-r', help='The runtime you want to use.',
              type=click.Choice(['local', 'remote']), required=True)
@click.option('--id', '-id', 'scan_id', help='Id of the scan or universe.', required=True)
def stop(runtime: str, scan_id: str) -> None:
    """Stop a scan.\n
    Usage:\n
        - ostorlab scan stop --runtime=source --id=id
    """

    if runtime == 'local':
        local.runtime.LocalRuntime().stop(scan_id=scan_id)
    else:
        # TODO (Rabson) add support for remote scans
        return
