"""Unittests for the source code scan create API requests."""

import json

from ostorlab.apis import source_code_scan_create

REPOSITORY = source_code_scan_create.Repository(
    id="1380473625",
    full_name="acme/demo",
    private=True,
    default_branch="main",
    url="https://github.com/acme/demo",
    provider="GITHUB",
)


def testRepositoriesAPIRequest_whenSearchProvided_shouldSendSearchAndPageSize() -> None:
    api_request = source_code_scan_create.RepositoriesAPIRequest(search="acme/demo")

    data = api_request.data

    assert "repositories(page: $page" in data["query"]
    assert json.loads(data["variables"]) == {
        "page": 1,
        "numberElements": source_code_scan_create.REPOSITORIES_PAGE_SIZE,
        "search": "acme/demo",
    }


def testRepositoriesAPIRequest_whenPageProvided_shouldSendPage() -> None:
    api_request = source_code_scan_create.RepositoriesAPIRequest(
        search="acme/demo", page=3
    )

    data = api_request.data

    assert json.loads(data["variables"])["page"] == 3


def testCreateSourceCodeScanAPIRequest_whenCommitProvided_shouldSendRepositoryAndCommit() -> (
    None
):
    api_request = source_code_scan_create.CreateSourceCodeScanAPIRequest(
        repository=REPOSITORY,
        scan_profile="Source Code Fast Scan",
        title="CI scan",
        commit_hash="0123abcd",
    )

    data = api_request.data

    assert "createSourceCodeScan(repository: $repository" in data["query"]
    assert json.loads(data["variables"]) == {
        "repository": {
            "id": "1380473625",
            "fullName": "acme/demo",
            "private": True,
            "defaultBranch": "main",
            "url": "https://github.com/acme/demo",
            "provider": "GITHUB",
        },
        "scanProfile": "Source Code Fast Scan",
        "title": "CI scan",
        "commitHash": "0123abcd",
        "branchName": None,
    }


def testCreateSourceCodeScanAPIRequest_whenBranchProvided_shouldSendBranchWithoutCommit() -> (
    None
):
    api_request = source_code_scan_create.CreateSourceCodeScanAPIRequest(
        repository=REPOSITORY,
        scan_profile="Source Code Fast Scan",
        branch_name="main",
    )

    variables = json.loads(api_request.data["variables"])

    assert variables["branchName"] == "main"
    assert variables["commitHash"] is None
