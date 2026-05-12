"""Tests for the `oxo scan run repository` CLI command, covering --file and --url options."""

from click import testing
from pytest_mock import plugin

from ostorlab.assets import repository as repository_asset
from ostorlab.cli import rootcli


def testScanRunRepository_whenNoOptionsProvided_shouldExitAndShowError(
    scan_run_cli_runner: testing.CliRunner,
) -> None:
    result = scan_run_cli_runner.invoke(
        rootcli.rootcli, ["scan", "run", "--agent=agent1", "repository"]
    )

    assert result.exit_code == 2
    assert "Command accepts either --file or --url." in result.output


def testScanRunRepository_whenUrlProvided_shouldCallScanWithRepositoryAsset(
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
            "--url",
            "https://storage.example.com/repo.zip",
            "--repo-url",
            "https://github.com/org/repo.git",
            "--commit-hash",
            "a1a10cdbc6551ba359169a3033f193b7f8c1b95d",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], repository_asset.Repository)
    assert assets[0].content_url == "https://storage.example.com/repo.zip"
    assert assets[0].repo_url == "https://github.com/org/repo.git"
    assert assets[0].commit_hash == "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"


def testScanRunRepository_whenFileProvided_shouldCallScanWithRepositoryAsset(
    scan_run_cli_runner: testing.CliRunner,
    mocker: plugin.MockerFixture,
    tmp_path,
) -> None:
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )
    archive = tmp_path / "repo.zip"
    archive.write_bytes(b"PK\x03\x04archive_content")

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "repository",
            "--file",
            str(archive),
            "--repo-url",
            "https://github.com/org/repo.git",
            "--commit-hash",
            "a1a10cdbc6551ba359169a3033f193b7f8c1b95d",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], repository_asset.Repository)
    assert assets[0].content == b"PK\x03\x04archive_content"
    assert assets[0].repo_url == "https://github.com/org/repo.git"
