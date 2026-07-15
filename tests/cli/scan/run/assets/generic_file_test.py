"""Tests for the `oxo scan run generic-file` CLI command."""

from click import testing
from pytest_mock import plugin

from ostorlab.assets import generic_file as generic_file_asset
from ostorlab.cli import rootcli


def testScanRunGenericFile_whenUrlProvided_callsScanWithAsset(
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
            "generic-file",
            "--url",
            "https://example.com/file.bin",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], generic_file_asset.GenericFile)
    assert assets[0].content_url == "https://example.com/file.bin"


def testScanRunGenericFile_whenFileProvided_callsScanWithAsset(
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
            "generic-file",
            "--file",
            "tests/__init__.py",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], generic_file_asset.GenericFile)
    assert assets[0].path == "tests/__init__.py"
    assert assets[0].content is not None


def testScanRunGenericFile_whenScanCreated_linksAgentGroupAndAssets(
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
            "generic-file",
            "--url",
            "https://example.com/file.bin",
        ],
    )

    assert result.exit_code == 0
    assert link_group_mocked.call_count == 1
    assert link_assets_mocked.call_count == 1
    assert link_assets_mocked.call_args[0][0] == 42


def testScanRunGenericFile_whenBothFileAndUrlProvided_shouldExitWithError(
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
            "generic-file",
            "--file",
            "tests/__init__.py",
            "--url",
            "https://example.com/file.bin",
        ],
    )

    assert result.exit_code == 2
    assert scan_mocked.call_count == 0


def testScanRunGenericFile_whenNoOptionProvided_shouldExitWithError(
    scan_run_cli_runner: testing.CliRunner,
    mocker: plugin.MockerFixture,
) -> None:
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "generic-file"],
    )

    assert result.exit_code == 2
    assert scan_mocked.call_count == 0
