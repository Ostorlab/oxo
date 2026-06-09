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
