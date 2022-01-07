"""Module for the command list inside the group scan.
This module takes care of listing all the remote or local scans.
Example of usage:
    - ostorlab scan list --source=source."""

import click
from ostorlab.cli.scan import scan
from ostorlab.apis import runner as apis_runner
from ostorlab.apis import scan_list
from ostorlab.cli import console

console = console.Console()


@scan.command()
@click.option('--runtime', '-r', help='The runtime you want to use.',
              type=click.Choice(['local', 'remote']), required=True)
@click.option('--page', '-p', help='Page number of scans you would like to see.', default=1)
@click.option('--elements', '-e', help='Number of scans to show per page.', default=10)
# Disabling pylint error of redfining built-in 'list'
# pylint: disable=redefined-builtin
def list(runtime: str, page: int, elements: int) -> None:
    """List all your scans.\n
    Usage:\n
        - ostorlab scan list --source=source
    """

    if runtime == 'remote':
        try:
            runner = apis_runner.APIRunner()
            with console.status('Fetching scans'):
                response = runner.execute(scan_list.ScansListAPIRequest(page, elements))
                console.success('Scans fetched successfully')
            columns = {'Id': 'id', 'Application': 'packageName', 'Version': 'version',
                        'Platform': 'assetType', 'Plan': 'plan', 'Created Time': 'createdTime',
                        'Progress': 'progress', 'Risk': 'riskRating'}
            scans = response['data']['scans']['scans']
            title = f'Showing {len(scans)} Scans'
            console.table(columns=columns, data=scans, table_title=title)
        except apis_runner.Error:
            console.error('Could not fetch scans.')
    else:
        # TODO (Rabson) add support for local scans
        return
