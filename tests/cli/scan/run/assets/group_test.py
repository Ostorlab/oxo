"""Tests for the `oxo scan run group` CLI command."""

from click import testing
from pytest_mock import plugin

from ostorlab.assets import android_apk as android_apk_asset
from ostorlab.assets import api_schema as api_schema_asset
from ostorlab.assets import domain_name as domain_name_asset
from ostorlab.assets import file as file_asset
from ostorlab.assets import ios_ipa as ios_ipa_asset
from ostorlab.assets import link as link_asset
from ostorlab.assets import repository as repository_asset
from ostorlab.cli import rootcli


def testScanRunGroup_whenMultipleAssetTypesProvided_callsScanWithAllAssets(
    scan_run_cli_runner: testing.CliRunner,
    mocker: plugin.MockerFixture,
) -> None:
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "group",
            "--apk",
            "https://cdn.example.com/app.apk",
            "--apk",
            "https://cdn.example.com/second-app.apk",
            "--ipa",
            "https://cdn.example.com/app.ipa",
            "--domain",
            "example.com",
            "--link",
            "https://app.example.com",
            "--link-method",
            "GET",
            "--repository-url",
            "https://github.com/org/repo",
            "--repository-commit-hash",
            "deadbeef",
            "--repository-provider",
            "github",
            "--file",
            "https://cdn.example.com/source.zip",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 7
    apk_urls = [
        a.content_url
        for a in assets
        if isinstance(a, android_apk_asset.AndroidApk) is True
    ]
    assert apk_urls == [
        "https://cdn.example.com/app.apk",
        "https://cdn.example.com/second-app.apk",
    ]
    assert any(isinstance(a, ios_ipa_asset.IOSIpa) is True for a in assets) is True
    domain = next(
        a for a in assets if isinstance(a, domain_name_asset.DomainName) is True
    )
    assert domain.name == "example.com"
    link = next(a for a in assets if isinstance(a, link_asset.Link) is True)
    assert link.url == "https://app.example.com"
    assert link.method == "GET"
    repository = next(
        a for a in assets if isinstance(a, repository_asset.Repository) is True
    )
    assert repository.repository_url == "https://github.com/org/repo"
    assert repository.commit_hash == "deadbeef"
    assert any(isinstance(a, file_asset.File) is True for a in assets) is True


def testScanRunGroup_whenLinkWithoutMethod_defaultsToGet(
    scan_run_cli_runner: testing.CliRunner,
    mocker: plugin.MockerFixture,
) -> None:
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "group",
            "--link",
            "https://app.example.com",
        ],
    )

    assert result.exit_code == 0
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], link_asset.Link) is True
    assert assets[0].method == "GET"


def testScanRunGroup_whenApiSchemaProvided_callsScanWithApiSchemaAsset(
    scan_run_cli_runner: testing.CliRunner,
    mocker: plugin.MockerFixture,
) -> None:
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "group",
            "--api-schema-endpoint",
            "https://api.example.com",
            "--api-schema-url",
            "https://api.example.com/openapi.json",
            "--api-schema-type",
            "openapi",
        ],
    )

    assert result.exit_code == 0
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], api_schema_asset.ApiSchema) is True
    assert assets[0].endpoint_url == "https://api.example.com"
    assert assets[0].content_url == "https://api.example.com/openapi.json"
    assert assets[0].schema_type == "openapi"


def testScanRunGroup_whenScanCreated_linksAgentGroupAndAssets(
    scan_run_cli_runner: testing.CliRunner,
    mocker: plugin.MockerFixture,
) -> None:
    created_scan = mocker.MagicMock(id=42)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.scan", return_value=created_scan)
    link_group_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.link_agent_group_scan"
    )
    link_assets_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.link_assets_scan"
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "group",
            "--domain",
            "example.com",
        ],
    )

    assert result.exit_code == 0
    assert link_group_mocked.call_count == 1
    assert link_assets_mocked.call_count == 1
    assert link_assets_mocked.call_args[0][0] == 42


def testScanRunGroup_whenNoAssetProvided_shouldExitWithError(
    scan_run_cli_runner: testing.CliRunner,
    mocker: plugin.MockerFixture,
) -> None:
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "group"],
    )

    assert result.exit_code == 2
    assert scan_mocked.call_count == 0


def testScanRunGroup_whenLinkMethodCountMismatch_shouldExitWithError(
    scan_run_cli_runner: testing.CliRunner,
    mocker: plugin.MockerFixture,
) -> None:
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "group",
            "--link",
            "https://app.example.com",
            "--link",
            "https://api.example.com",
            "--link-method",
            "GET",
        ],
    )

    assert result.exit_code == 2
    assert scan_mocked.call_count == 0
