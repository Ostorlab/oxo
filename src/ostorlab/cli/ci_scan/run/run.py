"""Module for the command run inside the group scan.
This module takes care of preparing the selected runtime and the lists of provided agents, before starting a scan.
Example of usage:
    - ostorlab scan run --agent=agent1 --agent=agent2 --title=test_scan [asset] [options]."""
import io
import logging
import multiprocessing
import click
import time

from ostorlab.cli.ci_scan.ci_scan import ci_scan
from ostorlab.apis.runners import runner as base_runner
from ostorlab.cli import console as cli_console
from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis import scan_create as scan_create_api
from ostorlab.apis import scan_info as scan_info_api

console = cli_console.Console()

logger = logging.getLogger(__name__)

MINUTE = 60
WAIT_MINUTES = 30
SLEEP_CHECKS = 10 # seconds

RATINGS_ORDER = {
    'high': 0,
    'medium': 1,
    'low': 2,
    'potentially': 3
}


@ci_scan.command()
@click.option('--plan', help='Scan plan to execute.', required=True)
@click.option('--file', type=click.File(mode='rb'), help='Path to .APK or IPA file.', required=True)
@click.option('--type', help='Scan type.', required=True)
@click.option('--title', help='Scan title.')
@click.option('--break_on_risk_rating', help='Fail if the scan risk rating is higher than the defined value.')
@click.option('--max_wait_minutes', help='Time to wait for the scan results.')
@click.pass_context
def run(ctx: click.core.Context, plan: str, file: io.FileIO,
            title: str, type: str, break_on_risk_rating: str = None, max_wait_minutes: int = WAIT_MINUTES) -> None:
    """Start a scan based on a plan in the CI.\n"""
    if ctx.obj.get('api_key'):
        with console.status('Starting the scan'):
            runner = authenticated_runner.AuthenticatedAPIRunner(api_key=ctx.obj.get('api_key'))
            try:
                scan_result = runner.execute(scan_create_api.CreateMobileScanAPIRequest(title=title,
                                                                              asset_type=scan_create_api.MobileAssetType[type.upper()],
                                                                              plan= scan_create_api.Plan[plan.upper()],
                                                                              application=file))
                scan_id = scan_result.get('data').get('scan').get('id')
                console.success(f'Scan created with id {scan_id}.')
                if break_on_risk_rating is not None:
                    apply_break_scan_risk_rating(break_on_risk_rating, scan_id, max_wait_minutes, runner)

            except base_runner.ResponseError as e:
                console.error(f'Could not start the scan. {e}')
                raise click.exceptions.Exit(2) from e
            except TimeoutError:
                console.error(f'The scan is still running')
                raise click.exceptions.Exit(2)
    else:
        console.error(f'API key not not provided.')
        raise click.exceptions.Exit(2)


def apply_break_scan_risk_rating(break_on_risk_rating, scan_id, max_wait_minutes, runner):
    if scan_create_api.RiskRating.has_value(break_on_risk_rating):
        check_scan_process = multiprocessing.Process(
            target=check_scan_periodically,
            args=(runner, scan_id, break_on_risk_rating)
        )
        check_scan_process.start()
        check_scan_process.join(int(max_wait_minutes) * MINUTE)

        if check_scan_process.is_alive():
            check_scan_process.kill()
            check_scan_process.join()
            raise TimeoutError()

        scan_result = runner.execute(scan_info_api.ScanInfoAPIRequest(scan_id=scan_id))
        if scan_result['data']['scan']['progress'] == 'done':
            scan_risk_rating = scan_result['data']['scan']['riskRating']
            check_scan_risk_rating(scan_risk_rating, break_on_risk_rating)
    else:
        console.error(f'Incorrect risk rating value. '
                      f'It should be one of {", ".join(scan_create_api.RiskRating.values())}')
        raise click.exceptions.Exit(2)


def check_scan_periodically(runner, scan_id):
    scan_done = False
    while not scan_done:
        scan_result = runner.execute(scan_info_api.ScanInfoAPIRequest(scan_id=scan_id))
        scan_progress = scan_result['data']['progress']
        if scan_progress == 'done':
            scan_done = True
        time.sleep(SLEEP_CHECKS)


def check_scan_risk_rating(scan_risk_rating, break_on_risk_rating):
    if scan_risk_rating in RATINGS_ORDER and RATINGS_ORDER[scan_risk_rating] < RATINGS_ORDER[break_on_risk_rating]:
        console.error(f'The scan risk rating is {scan_risk_rating}.')
        raise click.exceptions.Exit(2)
    else:
        console.success(f'Scan done with risk rating {scan_risk_rating}.')