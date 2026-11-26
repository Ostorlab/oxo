"""Asset of type repository.

This module resolves a repository reachable through the source code integrations of the organisation, then calls
the create source code scan API. The platform fetches the code itself, so nothing is uploaded from the CI.
"""

from typing import Any
from typing import cast

import click

from ostorlab.apis import source_code_scan_create as source_code_scan_create_api
from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis.runners import runner as base_runner
from ostorlab.cli.ci_scan.run import run
from ostorlab.cli.ci_scan.run.ci_logger import logger


class Error(Exception):
    """Base error of the repository asset."""


class RepositoryNotFoundError(Error):
    """The repository does not resolve to exactly one repository of the source code integrations."""


def _resolve_repository(
    runner: authenticated_runner.AuthenticatedAPIRunner, full_name: str
) -> source_code_scan_create_api.Repository:
    result = runner.execute(
        source_code_scan_create_api.RepositoriesAPIRequest(search=full_name)
    )
    # A repository reachable through several integrations of one provider (GitHub App and PAT) is listed once per
    # integration with the same provider and id.
    matches_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for repository in result["data"]["repositories"]["repositories"]:
        if repository["fullName"].lower() == full_name.lower():
            matches_by_key.setdefault(
                (repository["provider"], repository["id"]), repository
            )
    matches = list(matches_by_key.values())
    if len(matches) != 1:
        raise RepositoryNotFoundError(
            f"Expected one repository named {full_name} in the source code integrations of the organisation, "
            f"found {len(matches)}."
        )
    return source_code_scan_create_api.Repository(
        id=matches[0]["id"],
        full_name=matches[0]["fullName"],
        private=matches[0]["private"],
        default_branch=matches[0]["defaultBranch"],
        url=matches[0]["url"],
        provider=matches[0]["provider"],
    )


@run.run.command(name="repository")
@click.option(
    "--full-name",
    help="Full name of the repository to scan, for example `owner/name`.",
    required=True,
)
@click.option("--commit", help="Commit hash to scan.", required=False, default=None)
@click.option(
    "--branch",
    help="Branch to scan. The platform scans its head commit.",
    required=False,
    default=None,
)
@click.pass_context
def repository(
    ctx: click.core.Context, full_name: str, commit: str | None, branch: str | None
) -> None:
    """Run a source code scan of a repository reachable through a source code integration."""
    ci_logger = cast(logger.Logger, ctx.obj["ci_logger"])
    if (commit is None) == (branch is None):
        ci_logger.error("Set exactly one of --commit or --branch.")
        raise click.exceptions.Exit(2)

    scan_profile = ctx.obj["scan_profile"]
    title = ctx.obj["title"]
    break_on_risk_rating = ctx.obj["break_on_risk_rating"]
    runner = authenticated_runner.AuthenticatedAPIRunner(api_key=ctx.obj["api_key"])
    try:
        scan_result = runner.execute(
            source_code_scan_create_api.CreateSourceCodeScanAPIRequest(
                repository=_resolve_repository(runner, full_name),
                scan_profile=scan_profile,
                title=title,
                commit_hash=commit,
                branch_name=branch,
            )
        )
        scan_id = cast(
            int | str, scan_result["data"]["createSourceCodeScan"]["scan"]["id"]
        )
        ci_logger.output(name="scan_id", value=str(scan_id))
        ci_logger.info(f"Scan created with id {scan_id}.")

        if break_on_risk_rating is not None and break_on_risk_rating != "":
            run.apply_break_scan_risk_rating(
                break_on_risk_rating,
                scan_id,
                ctx.obj["max_wait_minutes"],
                runner,
                ci_logger,
            )
    except Error as error:
        ci_logger.error(str(error))
        raise click.exceptions.Exit(2) from error
    except base_runner.ResponseError as error:
        ci_logger.error(f"Could not start the scan. {error}")
        raise click.exceptions.Exit(2) from error
    except TimeoutError:
        ci_logger.error("The scan is still running.")
        raise click.exceptions.Exit(2) from None
