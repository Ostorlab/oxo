"""Common logic for Mobile Assets of type .APK package file AAB package file and IPA .
This module takes care of preparing the application file and calling the create mobile scan API.
"""

import io
import itertools
import json
from typing import List, Optional

import click

from ostorlab.cli.ci_scan.run import run
from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis.runners import runner as base_runner
from ostorlab.apis import scan_create as scan_create_api
from ostorlab.apis import test_credentials_create as test_credentials_create_api


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


def run_mobile_scan(
    ctx: click.core.Context,
    file: io.FileIO,
    asset_type: scan_create_api.MobileAssetType,
) -> None:
    """Create scan for mobile application package file."""
    ci_logger = ctx.obj["ci_logger"]
    if ctx.obj.get("api_key"):
        scan_profile = ctx.obj["scan_profile"]
        title = ctx.obj["title"]
        break_on_risk_rating = ctx.obj["break_on_risk_rating"]
        max_wait_minutes = ctx.obj["max_wait_minutes"]
        sboms = ctx.obj["sboms"]
        repository = ctx.obj["repository"]
        source = ctx.obj["source"]
        pr_number = ctx.obj["pr_number"]
        branch = ctx.obj["branch"]
        scope_urls_regexes = ctx.obj["scope_urls_regexes"]
        ui_prompt_ids = ctx.obj.get("ui_prompt_ids") or []
        ui_prompt_names = ctx.obj.get("ui_prompt_names") or []
        ui_prompt_actions = ctx.obj.get("ui_prompt_actions") or []
        runner = authenticated_runner.AuthenticatedAPIRunner(
            api_key=ctx.obj.get("api_key")
        )
        try:
            test_credentials = _prepare_test_credentials(ctx)
            if test_credentials:
                credential_ids = _create_test_credentials(test_credentials, runner)
                ci_logger.info(
                    f"Created test credentials {', '.join(str(t) for t in test_credentials)} successfully"
                )
            else:
                credential_ids = []

            ui_automation_rule_ids: List[int] = []

            if len(ui_prompt_ids) > 0:
                ui_automation_rule_ids.extend(ui_prompt_ids)
                ci_logger.info(f"Using existing UI prompts with IDs: {ui_prompt_ids}")

            if len(ui_prompt_names) > 0 and len(ui_prompt_actions) > 0:
                ui_prompts_json = [
                    {"name": name, "code": action}
                    for name, action in zip(ui_prompt_names, ui_prompt_actions)
                ]
                try:
                    ci_logger.info("Creating UI prompts...")
                    prompts_result = runner.execute(
                        scan_create_api.CreateUIPromptsAPIRequest(
                            ui_prompts=ui_prompts_json
                        )
                    )
                    created_prompt_ids = [
                        int(prompt["id"])
                        for prompt in prompts_result["data"]["createUiPrompts"][
                            "uiPrompts"
                        ]
                    ]
                    ui_automation_rule_ids.extend(created_prompt_ids)
                    ci_logger.info(f"Created UI prompts with IDs: {created_prompt_ids}")
                except (json.JSONDecodeError, KeyError) as e:
                    ci_logger.error(
                        f"Invalid UI prompts format: {e}. Continuing without UI prompts."
                    )

            ci_logger.info(
                f"creating scan `{title}` with profile `{scan_profile}` for `{asset_type}`"
            )
            scan_source = None
            if source is not None:
                scan_source = scan_create_api.ScanSource(
                    source=source,
                    repository=repository,
                    pr_number=pr_number,
                    branch=branch,
                )
            if scope_urls_regexes is not None and len(scope_urls_regexes) > 0:
                scope_urls_regexes = list(scope_urls_regexes)
            else:
                scope_urls_regexes = None

            scan_id = _create_scan(
                title=title,
                scan_profile=scan_profile,
                asset_type=asset_type,
                file=file,
                credential_ids=credential_ids,
                runner=runner,
                sboms=sboms,
                scan_source=scan_source,
                scope_urls_regexes=scope_urls_regexes,
                ui_automation_rule_ids=ui_automation_rule_ids,
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
    title: str,
    scan_profile: str,
    asset_type: scan_create_api.MobileAssetType,
    file: io.FileIO,
    credential_ids: List[int],
    runner: authenticated_runner.AuthenticatedAPIRunner,
    sboms: List[io.FileIO],
    scan_source: Optional[scan_create_api.ScanSource] = None,
    scope_urls_regexes: Optional[List[str]] = None,
    ui_automation_rule_ids: List[int] = (),
) -> int:
    scan_result = runner.execute(
        scan_create_api.CreateMobileScanAPIRequest(
            title=title,
            asset_type=asset_type,
            scan_profile=scan_profile,
            application=file,
            test_credential_ids=credential_ids,
            sboms=sboms,
            scan_source=scan_source,
            scope_urls_regexes=scope_urls_regexes,
            ui_automation_rule_ids=ui_automation_rule_ids,
        )
    )
    scan_id = scan_result.get("data").get("createMobileScan").get("scan").get("id")
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
