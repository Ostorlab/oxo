"""Tests for scan resume command."""

from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab.cli import rootcli
from ostorlab.runtimes.local import runtime as local_runtime


def testOstorlabScanResumeCLI_whenRuntimeIsLocal_resumesTheScan(
    mocker: plugin.MockerFixture,
) -> None:
    """The local runtime resumes the scan."""
    resume = mocker.patch.object(local_runtime.LocalRuntime, "resume")

    result = CliRunner().invoke(
        rootcli.rootcli, ["scan", "--runtime=local", "resume", "4"]
    )

    assert result.exit_code == 0
    resume.assert_called_once_with(scan_id=4)


def testOstorlabScanResumeCLI_whenScanIsNotPaused_showsTheErrorAndExits(
    mocker: plugin.MockerFixture,
) -> None:
    """A scan that is not paused reports why."""
    mocker.patch.object(
        local_runtime.LocalRuntime,
        "resume",
        side_effect=local_runtime.ScanResumeError("scan 4 is not paused."),
    )

    result = CliRunner().invoke(
        rootcli.rootcli, ["scan", "--runtime=local", "resume", "4"]
    )

    assert result.exit_code == 1
    assert "scan 4 is not paused." in result.output


def testOstorlabScanResumeCLI_whenStartFails_reportsTheScanIsStillPaused(
    mocker: plugin.MockerFixture,
) -> None:
    """A failed start keeps the scan paused, the user can resume it again."""
    mocker.patch.object(
        local_runtime.LocalRuntime,
        "resume",
        side_effect=local_runtime.SnapshotRestoreError("broken"),
    )

    result = CliRunner().invoke(
        rootcli.rootcli, ["scan", "--runtime=local", "resume", "4"]
    )

    assert result.exit_code == 1
    assert "it is still paused" in result.output


def testOstorlabScanResumeCLI_whenRuntimeIsNotLocal_raisesUsageError() -> None:
    """Only the local runtime can resume a scan."""
    result = CliRunner().invoke(
        rootcli.rootcli, ["scan", "--runtime=cloud", "resume", "4"]
    )

    assert result.exit_code != 0
    assert "only supported by the local runtime" in result.output
