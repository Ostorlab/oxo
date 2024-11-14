"""Asset of type link.
This module takes care of preparing a link before calling the create web scan API.
"""

import click
import itertools

from typing import List

from ostorlab.cli.ci_scan.run import run
from ostorlab.apis import scan_create as scan_create_api
from ostorlab.apis import test_credentials_create as test_credentials_create_api
from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis.runners import runner as base_runner


def _prepare_test_credentials(
    ctx: click.core.Context,
) -> List[test_credentials_create_api.TestCredential]:
    test_credentials_login = ctx.obj["test_credentials"]["test_credentials_login"]
    test_credentials_password = ctx.obj["test_credentials"]["test_credentials_password"]
    test_credentials_url = ctx.obj["test_credentials"]["test_credentials_url"]
    test_credentials_role = ctx.obj["test_credentials"]["test_credentials_role"]
    test_credentials_name = ctx.obj["test_credentials"]["test_credentials_name"]
    test_credentials_value = ctx.obj["test_credentials"]["test_credentials_value"]

    credentials = []
    for login, password, role, url in itertools.zip_longest(
        test_credentials_login,
        test_credentials_password,
        test_credentials_role,
        test_credentials_url,
    ):
        credentials.append(
            test_credentials_create_api.TestCredentialLogin(
                login=login, password=password, role=role, url=url
            )
        )

    if test_credentials_name:
        credentials.append(
            test_credentials_create_api.TestCredentialCustom(
                values=dict(
                    itertools.zip_longest(test_credentials_name, test_credentials_value)
                )
            )
        )

    return credentials


def run_link_scan(ctx: click.core.Context, url: List[str]) -> None:
    """Create scan for links."""
    ci_logger = ctx.obj["ci_logger"]
    if ctx.obj.get("api_key") is not None:
        scan_profile = ctx.obj["scan_profile"]
        title = ctx.obj["title"]
        break_on_risk_rating = ctx.obj["break_on_risk_rating"]
        max_wait_minutes = ctx.obj["max_wait_minutes"]
        sboms = ctx.obj["sboms"]
        api_schema = ctx.obj["api_schema"]
        filtered_url_regexes = ctx.obj["filtered_url_regexes"]
        proxy = ctx.obj["proxy"]
        qps = ctx.obj["qps"]
        runner = authenticated_runner.AuthenticatedAPIRunner(
            api_key=ctx.obj.get("api_key")
        )
        try:
            test_credentials = _prepare_test_credentials(ctx)
            if test_credentials:
                credential_ids = _create_test_credentials(test_credentials, runner)
                ci_logger.info(
                    f'Created test credentials {", ".join(str(t) for t in test_credentials)} successfully'
                )
            else:
                credential_ids = []

            ci_logger.info(
                f"creating Web scan `{title}` with profile `{scan_profile}`."
            )
            scan_id = _create_scan(
                title,
                scan_profile,
                url,
                credential_ids,
                runner,
                sboms,
                api_schema,
                filtered_url_regexes,
                proxy,
                qps,
            )

            ci_logger.output(name="scan_id", value=scan_id)
            ci_logger.info(f"Scan created with id {scan_id}.")

            if break_on_risk_rating is not None and break_on_risk_rating != "":
                run.apply_break_scan_risk_rating(
                    break_on_risk_rating, scan_id, max_wait_minutes, runner, ci_logger
                )

        except base_runner.ResponseError as e:
            ci_logger.error(f"Could not start the scan. {e}")
            raise click.exceptions.Exit(2) from e
        except TimeoutError:
            ci_logger.error("The scan is still running.")
            raise click.exceptions.Exit(2) from None
    else:
        ci_logger.error("API key not not provided.")
        raise click.exceptions.Exit(2) from None


def _create_scan(
    title,
    scan_profile,
    urls,
    credential_ids,
    runner,
    sboms,
    api_schema,
    filtered_url_regexes,
    proxy,
    qps,
):
    scan_result = runner.execute(
        scan_create_api.CreateWebScanAPIRequest(
            title=title,
            urls=urls,
            scan_profile=scan_profile,
            test_credential_ids=credential_ids,
            sboms=sboms,
            api_schema=api_schema,
            filtered_url_regexes=filtered_url_regexes,
            proxy=proxy,
            qps=qps,
        )
    )
    scan_id = scan_result.get("data").get("createWebScan").get("scan").get("id")
    return scan_id


def _create_test_credentials(test_credentials, runner):
    credential_ids = []
    for test_credential in test_credentials:
        test_credential_result = runner.execute(
            test_credentials_create_api.CreateTestCredentialAPIRequest(
                test_credential=test_credential
            )
        )
        credential_ids.append(
            test_credential_result.get("data")
            .get("createTestCredentials")
            .get("testCredentials")
            .get("id")
        )
    return credential_ids


@run.run.command()
@click.option("--url", help="List of Urls to scan.", required=True, multiple=True)
@click.pass_context
def link(ctx: click.core.Context, url: List[str]):
    """Run scan for links."""
    run_link_scan(ctx, url)
