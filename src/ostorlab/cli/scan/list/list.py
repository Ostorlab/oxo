"""Module for the command list inside the group scan.
This module takes care of listing all the remote or local scans.
Example of usage:
    - ostorlab scan list --source=source."""

import click
import logging
from ostorlab.cli.scan import scan
from ostorlab.apis import runner as apis_runner
from ostorlab.apis import scan_list

logger = logging.getLogger(__name__)


@scan.command()
@click.option('--source', '-s', type=click.Choice(['local', 'remote']), required=True)
def list(source: str) -> None:
    """List all your scans.\n
    Usage:\n
        - ostorlab scan list --source=source
    """

    if source == 'remote':
        try:
            runner = apis_runner.APIRunner()
            response = runner.execute(scan_list.ScansListAPIRequest())
            logger.info(response)
        except apis_runner.AuthenticationError:
            runner.unauthenticate()
    else:
        # TODO (Rabson) add support for local scans
        return
