"""Module for the command list inside the group scan.
This module takes care of listing all the remote or local scans.
Example of usage:
    - ostorlab scan list --source=source."""

import click
from ostorlab import runtimes
from ostorlab.cli.scan import scan
from ostorlab.apis import runner
from ostorlab.apis import scan_list


@scan.sc
@click.option('--source', '-s', type=click.Choice(['local', 'remote']), required=True)
def list(source: str) -> None:
    """List all your scans.\n
    Usage:\n
        - ostorlab scan list --source=source
    """

    if source == 'remote':
        runtime = runtimes.LocalRuntime()
    else:
        # TODO (Rabson) add support for local scans
        return
