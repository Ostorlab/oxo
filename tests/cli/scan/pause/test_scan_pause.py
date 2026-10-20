"""Tests for scan pause command."""

from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab import exceptions
from ostorlab.cli import rootcli
from ostorlab.runtimes.local import runtime as local_runtime


def testOstorlabScanPauseCLI_whenRuntimeIsLocal_pausesTheScan(
    mocker: plugin.MockerFixture,
) -> None:
    """The local runtime pauses the scan."""
    pause = mocker.patch.object(local_runtime.LocalRuntime, "pause")

    result = CliRunner().invoke(
        rootcli.rootcli, ["scan", "--runtime=local", "pause", "4"]
    )

    assert result.exit_code == 0
    pause.assert_called_once_with(scan_id=4)


def testOstorlabScanPauseCLI_whenPauseFails_showsTheErrorAndExits(
    mocker: plugin.MockerFixture,
) -> None:
    """A scan that cannot be paused reports why."""
    mocker.patch.object(
        local_runtime.LocalRuntime,
        "pause",
        side_effect=local_runtime.ScanPauseError("scan 4 is not running."),
    )

    result = CliRunner().invoke(
        rootcli.rootcli, ["scan", "--runtime=local", "pause", "4"]
    )

    assert result.exit_code == 1
    assert "scan 4 is not running." in result.output


def testOstorlabScanPauseCLI_whenDockerChecksFail_showsTheErrorAndExits(
    mocker: plugin.MockerFixture,
) -> None:
    """An error of the docker checks, like a swarm that cannot be initialized, is reported without a traceback."""
    mocker.patch.object(
        local_runtime.LocalRuntime,
        "pause",
        side_effect=exceptions.OstorlabError("swarm failed."),
    )

    result = CliRunner().invoke(
        rootcli.rootcli, ["scan", "--runtime=local", "pause", "4"]
    )

    assert result.exit_code == 1
    assert "swarm failed." in result.output


def testOstorlabScanPauseCLI_whenRuntimeIsNotLocal_raisesUsageError() -> None:
    """Only the local runtime can pause a scan."""
    result = CliRunner().invoke(
        rootcli.rootcli, ["scan", "--runtime=cloud", "pause", "4"]
    )

    assert result.exit_code != 0
    assert "only supported by the local runtime" in result.output
