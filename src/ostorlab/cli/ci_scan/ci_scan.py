"""Module for the command run inside the group scan.
This module takes care of preparing the selected runtime and the lists of provided agents, before starting a scan.
Example of usage:
    - ostorlab scan run --agent=agent1 --agent=agent2 --title=test_scan [asset] [options]."""
import io
import logging

import click

from ostorlab.cli.rootcli import rootcli
from ostorlab.apis.runners import runner as base_runner
from ostorlab.cli import console as cli_console
from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis import scan as scan_api

console = cli_console.Console()

logger = logging.getLogger(__name__)


@click.option('--api_key', help='API key to login to the platform.', required=True)
@click.option('--plan', help='Scan plan to execute.', required=True)
@click.option('--file', type=click.File(mode='rb'), help='Path to .APK or IPA file.', required=True)
@click.option('--type', help='Scan type.', required=True)
@click.option('--title', help='Scan title.')

@rootcli.command()
def ci_scan(api_key: str, plan: str, file: io.FileIO, title: str, type: str) -> None:
    """Start a scan based on a plan in the CI.\n"""

    with console.status('Starting the scan'):
        runner = authenticated_runner.AuthenticatedAPIRunner(api_key=api_key)
        try:
            runner.execute(scan_api.CreateMobileScanAPIRequest(title=title,
                                                                          asset_type=scan_api.MobileAssetType[type.upper()],
                                                                          plan= scan_api.Plan[plan.upper()],
                                                                          application=file.read()))
            console.success('Scan created.')
        except base_runner.ResponseError as e:
            console.error(f'Could not start the scan. {e}')
            raise click.exceptions.Exit(2) from e
