"""Module for the command list inside the group scan.
This module takes care of listing all the remote or local scans.
Example of usage:
    - ostorlab scan list --source=source."""

import click
from ostorlab.cli.scan import scan
from ostorlab.apis import runner as apis_runner
from ostorlab.apis import scan_list
from ostorlab.utils import rich_console


@scan.command()
@click.option('--source', '-s', help='Where you want your scans to be fetched from.',
type=click.Choice(['local', 'remote']), required=True)
@click.option('--page', '-p', help='Page number of scans you would like to see.', default=1)
@click.option('--elements', '-e', help='Number of scans to show per page.', default=10)

def list(source: str, page: int, elements: int) -> None:
    """List all your scans.\n
    Usage:\n
        - ostorlab scan list --source=source
    """

    if source == 'remote':
        try:
            runner = apis_runner.APIRunner()
            response = runner.execute(scan_list.ScansListAPIRequest(page, elements))
            rich_console.scan_list_table(response)
        except apis_runner.Error:
            rich_console.error('Could not fetch scans.')
    else:
        # TODO (Rabson) add support for local scans
        return
