"""Module for the command run inside the group ci_scan.
Example of usage:
- ostorlab --api_key='myKey' ci_scan run --plan=free --break_on_risk_rating=medium --title=test_scan [asset] [options].
"""
import logging
import multiprocessing
import click
import time

from ostorlab.cli.ci_scan.ci_scan import ci_scan
from ostorlab.cli import console as cli_console
from ostorlab.apis import scan_create as scan_create_api
from ostorlab.apis import scan_info as scan_info_api
from ostorlab.cli.ci_scan.run.ci_logger import console_logger, github_logger

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

CI_LOGGER = {
    'console': console_logger.Logger(),
    'github': github_logger.Logger()
}

@ci_scan.group()
@click.option('--plan', help='Scan plan to execute.', required=True)
@click.option('--title', help='Scan title.')
@click.option('--break_on_risk_rating', help='Fail if the scan risk rating is higher than the defined value.')
@click.option('--max_wait_minutes', help='Time to wait for the scan results.', required=False, default=WAIT_MINUTES)
@click.option('--log_flavor', help='Type of expected output based on the CI.', required=False, default='console')
@click.pass_context
def run(ctx: click.core.Context, plan: str, title: str,
        break_on_risk_rating: str, max_wait_minutes: int, log_flavor: str) -> None:
    """Start a scan based on a plan in the CI.\n"""
    if log_flavor not in CI_LOGGER:
        CI_LOGGER['console'].error(f'log_flavor value {log_flavor} not supported. Possible options: {CI_LOGGER.keys()}')
    else:
        ci_logger = CI_LOGGER.get(log_flavor)

    if not ctx.obj.get('api_key'):
        ci_logger.error('API key not not provided.')
        raise click.exceptions.Exit(2)

    ctx.obj['plan'] = plan
    ctx.obj['title'] = title
    ctx.obj['break_on_risk_rating'] = break_on_risk_rating
    ctx.obj['max_wait_minutes'] = max_wait_minutes
    ctx.obj['ci_logger'] = ci_logger


def apply_break_scan_risk_rating(break_on_risk_rating, scan_id, max_wait_minutes, runner, ci_logger):
    """Wait for the scan to finish and raise an exception if its risk is higher than the defined value."""
    if scan_create_api.RiskRating.has_value(break_on_risk_rating):
        check_scan_process = multiprocessing.Process(
            target=check_scan_periodically,
            args=(runner, scan_id)
        )
        check_scan_process.start()
        check_scan_process.join(int(max_wait_minutes)*MINUTE)

        if check_scan_process.is_alive():
            check_scan_process.kill()
            check_scan_process.join()
            raise TimeoutError()

        scan_result = runner.execute(scan_info_api.ScanInfoAPIRequest(scan_id=scan_id))
        if scan_result['data']['scan']['progress'] == 'done':
            scan_risk_rating = scan_result['data']['scan']['riskRating']
            check_scan_risk_rating(scan_risk_rating, break_on_risk_rating, ci_logger)
    else:
        ci_logger.error(f'Incorrect risk rating value. '
                      f'It should be one of {", ".join(scan_create_api.RiskRating.values())}')
        raise click.exceptions.Exit(2)


def check_scan_periodically(runner, scan_id):
    """Retrieve the scan progress using the API and wait if the progress is different than done"""
    scan_done = False
    while not scan_done:
        scan_result = runner.execute(scan_info_api.ScanInfoAPIRequest(scan_id=scan_id))
        scan_progress = scan_result['data']['scan']['progress']
        if scan_progress == 'done':
            scan_done = True
        time.sleep(SLEEP_CHECKS)


def check_scan_risk_rating(scan_risk_rating, break_on_risk_rating, ci_logger):
    """Compare the scan risk and raise an exception if the scan risk is higher than the defined value"""
    if scan_risk_rating in RATINGS_ORDER and RATINGS_ORDER[scan_risk_rating] < RATINGS_ORDER[break_on_risk_rating]:
        ci_logger.error(f'The scan risk rating is {scan_risk_rating}.')
        raise click.exceptions.Exit(2)
    else:
        ci_logger.info(f'Scan done with risk rating {scan_risk_rating}.')
