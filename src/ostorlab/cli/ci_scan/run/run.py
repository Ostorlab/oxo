"""Module for the command run inside the group ci_scan.
Example of usage:
- ostorlab --api-key='myKey' ci-scan run --scan-profile=full_scan \
           --break-on-risk-rating=medium --title=test_scan [asset] [options].
"""

import io
import multiprocessing
import click
import time
from typing import List

from ostorlab.cli.ci_scan.ci_scan import ci_scan
from ostorlab.apis import scan_create as scan_create_api
from ostorlab.apis import scan_info as scan_info_api
from ostorlab.apis.runners import authenticated_runner
from ostorlab.cli.ci_scan.run.ci_logger import (
    console_logger,
    github_logger,
    circleci_logger,
    logger,
)
from ostorlab.utils import risk_rating

MINUTE = 60
WAIT_MINUTES = 30
SLEEP_CHECKS = 10  # seconds
SCAN_PROGRESS_NOT_STARTED = "not_started"
SCAN_PROGRESS_DONE = "done"

CI_LOGGER = {
    "console": console_logger.Logger,
    "github": github_logger.Logger,
    "circleci": circleci_logger.Logger,
}


@ci_scan.group()
@click.option("--scan-profile", help="Scan profile to execute.", required=True)
@click.option("--title", help="Scan title.")
@click.option(
    "--break-on-risk-rating",
    help="Fail if the scan risk rating is higher than the defined value.",
)
@click.option(
    "--max-wait-minutes",
    help="Time to wait for the scan results.",
    required=False,
    default=WAIT_MINUTES,
)
@click.option(
    "--log-flavor",
    help="Type of expected output based on the CI.",
    required=False,
    default="console",
)
@click.option(
    "--test-credentials-login",
    help="Test credentials login, composed of login, password, url (optional) and role (optional).",
    required=False,
    multiple=True,
)
@click.option(
    "--test-credentials-password",
    help="Test credentials login, composed of login, password, url (optional) and role (optional).",
    required=False,
    multiple=True,
)
@click.option(
    "--test-credentials-url",
    help="Test credentials login, composed of login, password, url (optional) and role (optional).",
    required=False,
    multiple=True,
)
@click.option(
    "--test-credentials-role",
    help="Test credentials login, composed of login, password, url (optional) and role (optional).",
    required=False,
    multiple=True,
)
@click.option(
    "--test-credentials-name",
    help="Test custom credentials, composed of name and value.",
    required=False,
    multiple=True,
)
@click.option(
    "--test-credentials-value",
    help="Test custom credentials, composed of name and value.",
    required=False,
    multiple=True,
)
@click.option(
    "--sbom",
    "sboms",
    help="Path to sbom file.",
    type=click.File(mode="rb"),
    required=False,
    multiple=True,
    default=[],
)
@click.pass_context
def run(
    ctx: click.core.Context,
    scan_profile: str,
    title: str,
    break_on_risk_rating: str,
    max_wait_minutes: int,
    log_flavor: str,
    test_credentials_login: List[str],
    test_credentials_password: List[str],
    test_credentials_url: List[str],
    test_credentials_role: List[str],
    test_credentials_name: List[str],
    test_credentials_value: List[str],
    sboms: List[io.FileIO],
) -> None:
    """Start a scan based on a scan profile in the CI.\n"""

    if log_flavor not in CI_LOGGER:
        CI_LOGGER["console"]().error(
            f"log_flavor value {log_flavor} not supported."
            f" Possible options: {CI_LOGGER.keys()}"
        )
        raise click.exceptions.Exit(2)

    ci_logger = CI_LOGGER.get(log_flavor)()

    if len(test_credentials_login) != len(test_credentials_password):
        ci_logger.error("Loging and password credentials are not matching count.")
        raise click.exceptions.Exit(2)

    if len(test_credentials_name) != len(test_credentials_value):
        ci_logger.error("Name and value credentials are not matching count.")
        raise click.exceptions.Exit(2)

    if not ctx.obj.get("api_key"):
        ci_logger.error("API key not not provided.")
        raise click.exceptions.Exit(2)

    if scan_profile in scan_create_api.SCAN_PROFILES:
        ctx.obj["scan_profile"] = scan_create_api.SCAN_PROFILES[scan_profile]
    else:
        ci_logger.error(
            f"Scan profile {scan_profile} not supported. Possible options: {scan_create_api.SCAN_PROFILES.keys()}"
        )
        raise click.exceptions.Exit(2)

    ctx.obj["title"] = title
    ctx.obj["break_on_risk_rating"] = break_on_risk_rating
    ctx.obj["max_wait_minutes"] = max_wait_minutes
    ctx.obj["ci_logger"] = ci_logger
    ctx.obj["test_credentials"] = {
        "test_credentials_login": test_credentials_login,
        "test_credentials_password": test_credentials_password,
        "test_credentials_url": test_credentials_url,
        "test_credentials_role": test_credentials_role,
        "test_credentials_name": test_credentials_name,
        "test_credentials_value": test_credentials_value,
    }
    ctx.obj["sboms"] = sboms


def apply_break_scan_risk_rating(
    break_on_risk_rating: str,
    scan_id: int,
    max_wait_minutes: int,
    runner: authenticated_runner.AuthenticatedAPIRunner,
    ci_logger: logger.Logger,
):
    """Wait for the scan to finish and raise an exception if its risk is higher than the defined value."""
    if risk_rating.RiskRating.has_value(break_on_risk_rating.upper()):
        # run the check on a separate process and join it with a timeout. An exception is raised after the timeout.
        check_scan_process = multiprocessing.Process(
            target=_check_scan_periodically, args=(runner, scan_id)
        )
        check_scan_process.start()
        check_scan_process.join(int(max_wait_minutes) * MINUTE)

        if check_scan_process.is_alive():
            check_scan_process.kill()
            check_scan_process.join()
            _handle_scan_timeout(runner, scan_id, break_on_risk_rating, ci_logger)

        scan_result = runner.execute(scan_info_api.ScanInfoAPIRequest(scan_id=scan_id))
        if scan_result["data"]["scan"]["progress"] == "done":
            scan_risk_rating = scan_result["data"]["scan"]["riskRating"]
            _check_scan_risk_rating(scan_risk_rating, break_on_risk_rating, ci_logger)
    else:
        ci_logger.error(
            f"Incorrect risk rating value {break_on_risk_rating}. "
            f'It should be one of {", ".join(risk_rating.RiskRating.values())}'
        )
        raise click.exceptions.Exit(2)


def _check_scan_periodically(
    runner: authenticated_runner.AuthenticatedAPIRunner, scan_id: int
) -> None:
    """Retrieve the scan progress using the API and wait if the progress is different than done"""
    scan_done = False
    while not scan_done:
        scan_result = runner.execute(scan_info_api.ScanInfoAPIRequest(scan_id=scan_id))
        scan_progress = scan_result["data"]["scan"]["progress"]
        if scan_progress == "done":
            scan_done = True
        time.sleep(SLEEP_CHECKS)


def _check_scan_risk_rating(
    scan_risk_rating: str, break_on_risk_rating, ci_logger: logger.Logger
) -> None:
    """Compare the scan risk and raise an exception if the scan risk is higher than the defined value"""
    if _is_scan_risk_rating_higher(scan_risk_rating, break_on_risk_rating):
        ci_logger.error(f"The scan risk rating is {scan_risk_rating}.")
        raise click.exceptions.Exit(2)
    else:
        ci_logger.info(f"Scan done with risk rating {scan_risk_rating}.")


def _is_scan_risk_rating_higher(
    scan_risk_rating: str, break_on_risk_rating: str
) -> bool:
    """Returns a boolean of the scan risk Comparison with the defined break value"""
    return (
        scan_risk_rating.upper() in risk_rating.RATINGS_ORDER
        and risk_rating.RATINGS_ORDER[scan_risk_rating.upper()]
        < risk_rating.RATINGS_ORDER[break_on_risk_rating.upper()]
    )


def _handle_scan_timeout(
    runner: authenticated_runner.AuthenticatedAPIRunner,
    scan_id: int,
    break_on_risk_rating: str,
    ci_logger: logger.Logger,
) -> None:
    """when the scan triggers a timeout, we check if the scan has started and if the risk rating is higher
    than the defined break value. In this case we report the risk rating, and we exit code 2
    otherwise we raise the timeout exception
    """
    scan_result = runner.execute(scan_info_api.ScanInfoAPIRequest(scan_id=scan_id))
    if scan_result["data"]["scan"]["progress"] != SCAN_PROGRESS_NOT_STARTED:
        scan_risk_rating = scan_result["data"]["scan"]["riskRating"]
        if scan_risk_rating is not None and _is_scan_risk_rating_higher(
            scan_risk_rating, break_on_risk_rating
        ):
            ci_logger.error(f"The scan risk rating is {scan_risk_rating}.")
            raise click.exceptions.Exit(2)
    raise TimeoutError()
