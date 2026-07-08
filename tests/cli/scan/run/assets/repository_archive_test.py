"""Tests for the `oxo scan run repository-archive` CLI command."""

from click import testing
from pytest_mock import plugin

from ostorlab.assets import repository_archive as repository_archive_asset
from ostorlab.cli import rootcli


def testScanRunRepositoryArchive_whenUrlProvided_callsScanWithAsset(
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
            "repository-archive",
            "--url",
            "https://example.com/source-archive.tar.gz",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], repository_archive_asset.RepositoryArchive)
    assert assets[0].content_url == "https://example.com/source-archive.tar.gz"


def testScanRunRepositoryArchive_whenFileProvided_callsScanWithAsset(
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
            "repository-archive",
            "--file",
            "tests/__init__.py",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], repository_archive_asset.RepositoryArchive)
    assert assets[0].path == "tests/__init__.py"
    assert assets[0].content is not None


def testScanRunRepositoryArchive_whenScanCreated_linksAgentGroupAndAssets(
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
            "repository-archive",
            "--url",
            "https://example.com/source-archive.tar.gz",
        ],
    )

    assert result.exit_code == 0
    assert link_group_mocked.call_count == 1
    assert link_assets_mocked.call_count == 1
    assert link_assets_mocked.call_args[0][0] == 42


def testScanRunRepositoryArchive_whenBothFileAndUrlProvided_shouldExitWithError(
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
            "repository-archive",
            "--file",
            "tests/__init__.py",
            "--url",
            "https://example.com/source-archive.tar.gz",
        ],
    )

    assert result.exit_code == 2
    assert scan_mocked.call_count == 0


def testScanRunRepositoryArchive_whenNoOptionProvided_shouldExitWithError(
    scan_run_cli_runner: testing.CliRunner,
    mocker: plugin.MockerFixture,
) -> None:
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "repository-archive"],
    )

    assert result.exit_code == 2
    assert scan_mocked.call_count == 0
