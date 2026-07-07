"""Tests for the `oxo scan run repository` CLI command."""

from click import testing
from pytest_mock import plugin

from ostorlab.assets import repository as repository_asset
from ostorlab.cli import rootcli


def testScanRunRepository_whenRepositoryUrlProvided_callsScanWithRepositoryAsset(
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
            "repository",
            "--repository-url",
            "https://github.com/org/repo.git",
            "--commit-hash",
            "a1a10cdbc6551ba359169a3033f193b7f8c1b95d",
            "--provider",
            "gitlab",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], repository_asset.Repository)
    assert assets[0].repository_url == "https://github.com/org/repo.git"
    assert assets[0].commit_hash == "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"
    assert assets[0].provider == "GITLAB"


def testScanRunRepository_whenContentUrlProvided_callsScanWithRepositoryAsset(
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
            "repository",
            "--content-url",
            "https://example.com/source-archive.tar.gz",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], repository_asset.Repository)
    assert assets[0].content_url == "https://example.com/source-archive.tar.gz"
    assert assets[0].repository_url == ""


def testScanRunRepository_whenBothRepositoryUrlAndContentUrlProvided_shouldFail(
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
            "repository",
            "--repository-url",
            "https://github.com/org/repo.git",
            "--content-url",
            "https://example.com/source-archive.tar.gz",
        ],
    )

    assert result.exit_code != 0
    assert scan_mocked.call_count == 0


def testScanRunRepository_whenNeitherUrlProvided_shouldFail(
    scan_run_cli_runner: testing.CliRunner,
    mocker: plugin.MockerFixture,
) -> None:
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "repository"],
    )

    assert result.exit_code != 0
    assert scan_mocked.call_count == 0


def testScanRunRepository_whenGitFieldsIncomplete_shouldFail(
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
            "repository",
            "--repository-url",
            "https://github.com/org/repo.git",
        ],
    )

    assert result.exit_code != 0
    assert scan_mocked.call_count == 0
