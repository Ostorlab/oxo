"""Tests for the repository asset of the ci-scan run command."""

import json
import multiprocessing
import re
from typing import Any

from click import testing as click_testing
from pytest_mock import plugin

from ostorlab.apis import source_code_scan_create
from ostorlab.apis.runners import runner as base_runner
from ostorlab.cli import rootcli

EXECUTE_PATH = (
    "ostorlab.apis.runners.authenticated_runner.AuthenticatedAPIRunner.execute"
)
REPOSITORY = {
    "id": "1380473625",
    "fullName": "acme/demo",
    "private": True,
    "defaultBranch": "main",
    "url": "https://github.com/acme/demo",
    "provider": "GITHUB",
}
SCAN_CREATED = {"data": {"createSourceCodeScan": {"scan": {"id": "7"}}}}


def _repositories_result(*repositories: dict[str, Any]) -> dict[str, Any]:
    return {"data": {"repositories": {"repositories": list(repositories)}}}


def _scan_info_result(progress: str, risk_rating: str | None) -> dict[str, Any]:
    return {"data": {"scan": {"progress": progress, "riskRating": risk_rating}}}


def _normalize_output(text: str) -> str:
    """Strip ANSI escape sequences and the line wrapping of the console."""
    return " ".join(re.sub(r"\x1b\[[0-9;]*m", "", text).split())


def _invoke(*args: str) -> click_testing.Result:
    return click_testing.CliRunner().invoke(
        rootcli.rootcli, ["--api-key=12", "ci-scan", "run", *args]
    )


def testRepositoryScan_whenCommitProvided_shouldCreateScanOfResolvedRepository(
    mocker: plugin.MockerFixture,
) -> None:
    execute = mocker.patch(
        EXECUTE_PATH, side_effect=[_repositories_result(REPOSITORY), SCAN_CREATED]
    )

    result = _invoke(
        "--scan-profile=source_code_fast_scan",
        "--title=CI scan",
        "repository",
        "--full-name=Acme/Demo",
        "--commit=0123abcd",
    )

    assert result.exit_code == 0, result.output
    assert "Scan created with id 7." in _normalize_output(result.output)
    search_variables = json.loads(execute.call_args_list[0].args[0].data["variables"])
    assert search_variables["search"] == "Acme/Demo"
    create_variables = json.loads(execute.call_args_list[1].args[0].data["variables"])
    assert create_variables["repository"] == REPOSITORY
    assert create_variables["commitHash"] == "0123abcd"
    assert create_variables["branchName"] is None
    assert create_variables["scanProfile"] == "Source Code Fast Scan"
    assert create_variables["title"] == "CI scan"


def testRepositoryScan_whenRepositoryNotReachable_shouldExitWithoutCreatingScan(
    mocker: plugin.MockerFixture,
) -> None:
    execute = mocker.patch(EXECUTE_PATH, side_effect=[_repositories_result()])

    result = _invoke(
        "--scan-profile=source_code_fast_scan",
        "--title=CI scan",
        "repository",
        "--full-name=acme/demo",
        "--branch=main",
    )

    assert result.exit_code == 2
    assert (
        "Expected one repository named acme/demo in the source code integrations of the organisation, found 0."
        in _normalize_output(result.output)
    )
    assert execute.call_count == 1


def testRepositoryScan_whenNameMatchesSeveralRepositories_shouldExitWithoutCreatingScan(
    mocker: plugin.MockerFixture,
) -> None:
    gitlab_repository = {**REPOSITORY, "id": "42", "provider": "GITLAB"}
    execute = mocker.patch(
        EXECUTE_PATH,
        side_effect=[_repositories_result(REPOSITORY, gitlab_repository)],
    )

    result = _invoke(
        "--scan-profile=source_code_fast_scan",
        "--title=CI scan",
        "repository",
        "--full-name=acme/demo",
        "--branch=main",
    )

    assert result.exit_code == 2
    assert "found 2." in _normalize_output(result.output)
    assert execute.call_count == 1


def testRepositoryScan_whenRepositoryListedByTwoIntegrations_shouldCreateScanOnce(
    mocker: plugin.MockerFixture,
) -> None:
    execute = mocker.patch(
        EXECUTE_PATH,
        side_effect=[_repositories_result(REPOSITORY, dict(REPOSITORY)), SCAN_CREATED],
    )

    result = _invoke(
        "--scan-profile=source_code_fast_scan",
        "--title=CI scan",
        "repository",
        "--full-name=acme/demo",
        "--commit=0123abcd",
    )

    assert result.exit_code == 0, result.output
    assert execute.call_count == 2
    create_variables = json.loads(execute.call_args_list[1].args[0].data["variables"])
    assert create_variables["repository"] == REPOSITORY


def testRepositoryScan_whenRepositoryIsPastFirstSearchPage_shouldCreateScanOfIt(
    mocker: plugin.MockerFixture,
) -> None:
    similar_repositories = [
        {**REPOSITORY, "id": str(index), "fullName": f"acme/demo-{index}"}
        for index in range(source_code_scan_create.REPOSITORIES_PAGE_SIZE)
    ]
    execute = mocker.patch(
        EXECUTE_PATH,
        side_effect=[
            _repositories_result(*similar_repositories),
            _repositories_result(REPOSITORY),
            SCAN_CREATED,
        ],
    )

    result = _invoke(
        "--scan-profile=source_code_fast_scan",
        "--title=CI scan",
        "repository",
        "--full-name=acme/demo",
        "--commit=0123abcd",
    )

    assert result.exit_code == 0, result.output
    second_search_variables = json.loads(
        execute.call_args_list[1].args[0].data["variables"]
    )
    assert second_search_variables["page"] == 2
    create_variables = json.loads(execute.call_args_list[2].args[0].data["variables"])
    assert create_variables["repository"] == REPOSITORY


def testRepositoryScan_whenCommitAndBranchBothProvided_shouldExitWithError(
    mocker: plugin.MockerFixture,
) -> None:
    execute = mocker.patch(EXECUTE_PATH)

    result = _invoke(
        "--scan-profile=source_code_fast_scan",
        "--title=CI scan",
        "repository",
        "--full-name=acme/demo",
        "--commit=0123abcd",
        "--branch=main",
    )

    assert result.exit_code == 2
    assert "Set exactly one of --commit or --branch." in _normalize_output(
        result.output
    )
    assert execute.call_count == 0


def testRepositoryScan_whenRiskRatingAboveThreshold_shouldExitWithError(
    mocker: plugin.MockerFixture,
) -> None:
    mocker.patch("time.sleep")
    scan_info = _scan_info_result("done", "high")
    mocker.patch(
        EXECUTE_PATH,
        side_effect=[
            _repositories_result(REPOSITORY),
            SCAN_CREATED,
            scan_info,
            scan_info,
        ],
    )

    result = _invoke(
        "--scan-profile=source_code_fast_scan",
        "--title=CI scan",
        "--break-on-risk-rating=medium",
        "repository",
        "--full-name=acme/demo",
        "--commit=0123abcd",
    )

    assert result.exit_code == 2
    assert "The scan risk rating is high." in _normalize_output(result.output)


def testRepositoryScan_whenScanErrors_shouldExitWithErrorStatus(
    mocker: plugin.MockerFixture,
) -> None:
    mocker.patch("time.sleep")
    scan_info = _scan_info_result("error", None)
    mocker.patch(
        EXECUTE_PATH,
        side_effect=[
            _repositories_result(REPOSITORY),
            SCAN_CREATED,
            scan_info,
            scan_info,
        ],
    )

    result = _invoke(
        "--scan-profile=source_code_fast_scan",
        "--title=CI scan",
        "--break-on-risk-rating=high",
        "repository",
        "--full-name=acme/demo",
        "--commit=0123abcd",
    )

    assert result.exit_code == 2
    assert "The scan ended with status error before completing." in _normalize_output(
        result.output
    )


def testRepositoryScan_whenBranchProvided_shouldCreateScanOfBranch(
    mocker: plugin.MockerFixture,
) -> None:
    execute = mocker.patch(
        EXECUTE_PATH, side_effect=[_repositories_result(REPOSITORY), SCAN_CREATED]
    )

    result = _invoke(
        "--scan-profile=source_code_fast_scan",
        "--title=CI scan",
        "repository",
        "--full-name=acme/demo",
        "--branch=release",
    )

    assert result.exit_code == 0, result.output
    assert "Scan created with id 7." in _normalize_output(result.output)
    create_variables = json.loads(execute.call_args_list[1].args[0].data["variables"])
    assert create_variables["branchName"] == "release"
    assert create_variables["commitHash"] is None


def testRepositoryScan_whenScanCreationRejected_shouldExitWithError(
    mocker: plugin.MockerFixture,
) -> None:
    mocker.patch(
        EXECUTE_PATH,
        side_effect=[
            _repositories_result(REPOSITORY),
            base_runner.ResponseError("Repository is archived."),
        ],
    )

    result = _invoke(
        "--scan-profile=source_code_fast_scan",
        "--title=CI scan",
        "repository",
        "--full-name=acme/demo",
        "--commit=0123abcd",
    )

    assert result.exit_code == 2
    assert "Could not start the scan. Repository is archived." in _normalize_output(
        result.output
    )


def testRepositoryScan_whenScanStillRunningAfterMaxWait_shouldExitWithError(
    mocker: plugin.MockerFixture,
) -> None:
    mocker.patch(
        EXECUTE_PATH,
        side_effect=[
            _repositories_result(REPOSITORY),
            SCAN_CREATED,
            _scan_info_result("in_progress", None),
        ],
    )
    process_mock = mocker.patch.object(multiprocessing, "Process")
    process_mock.return_value.is_alive.return_value = True

    result = _invoke(
        "--scan-profile=source_code_fast_scan",
        "--title=CI scan",
        "--break-on-risk-rating=medium",
        "--max-wait-minutes=1",
        "repository",
        "--full-name=acme/demo",
        "--commit=0123abcd",
    )

    assert result.exit_code == 2
    assert "The scan is still running." in _normalize_output(result.output)
