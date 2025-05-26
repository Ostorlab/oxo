"""Tests for scan stop command."""

from unittest import mock

import pytest
from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab.apis.runners import authenticated_runner
from ostorlab.cli import rootcli
from ostorlab.runtimes.local import runtime as local_runtime


def testOstorlabScanStopCLI_whenRuntimeIsRemoteAndScanIdIsValid_stopsScan(
    httpx_mock,
):
    """Test ostorlab scan stop command with valid scan id.
    Should stop the scan with the given scan id.
    """

    scan_data = {"data": {"stopScan": {"scan": {"id": "123456"}}}}

    runner = CliRunner()
    httpx_mock.add_response(
        method="POST",
        url=authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=scan_data,
        status_code=200,
    )
    result = runner.invoke(
        rootcli.rootcli, ["scan", "--runtime=cloud", "stop", "123456"]
    )

    assert result.exception is None
    assert "Scan stopped successfully" in result.output


def testOstorlabScanStopCLI_whenRuntimeIsRemoteAndScanIdIsInValid_stopsScan(
    httpx_mock,
):
    """Test ostorlab scan stop command with invalid scan id.
    Should show error message.
    """

    scan_data = {"errors": [{"message": "Scan matching query does not exist."}]}

    runner = CliRunner()
    httpx_mock.add_response(
        method="POST",
        url=authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=scan_data,
        status_code=200,
    )
    result = runner.invoke(
        rootcli.rootcli, ["scan", "--runtime=cloud", "stop", "123456"]
    )

    assert result.exception is None
    assert "Could not stop scan" in result.output


@mock.patch.object(local_runtime.LocalRuntime, "stop")
def testOstorlabScanStopCLI_whenRuntimeIsLocal_callsStopMethodWithProvidedId(
    mock_scan_stop, mocker
):
    """Test ostorlab scan stop command with a scan id.
    Should call stop method with provided scan id.
    """

    mock_scan_stop.return_value = None
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    runner = CliRunner()

    runner.invoke(rootcli.rootcli, ["scan", "--runtime=local", "stop", "123456"])

    mock_scan_stop.assert_called_once_with(scan_id=123456)


@mock.patch.object(local_runtime.LocalRuntime, "stop")
def testOstorlabScanStopCLI_whenMultipleScanIdsAreProvided_stopsAllProvidedScans(
    mock_scan_stop: mock.Mock, mocker: plugin.MockerFixture
) -> None:
    """Test ostorlab scan stop command with multiple scan ids.
    Should call stop method for each provided scan id.
    """

    mock_scan_stop.return_value = None
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli, ["scan", "--runtime=local", "stop", "1", "2", "3"]
    )

    assert result.exception is None
    assert "Stopping 3 scan(s)" in result.output
    assert mock_scan_stop.call_count == 3
    mock_scan_stop.assert_any_call(scan_id=1)
    mock_scan_stop.assert_any_call(scan_id=2)
    mock_scan_stop.assert_any_call(scan_id=3)


@mock.patch.object(local_runtime.LocalRuntime, "stop")
@mock.patch.object(local_runtime.LocalRuntime, "list")
def testOstorlabScanStopCLI_whenStopAllIsUsedAndScansExist_stopsAllScans(
    mock_list_scans: mock.Mock, mock_scan_stop: mock.Mock, mocker: plugin.MockerFixture
) -> None:
    """Test ostorlab scan stop command with --all flag.
    Should stop all running scans.
    """

    mock_list_scans.return_value = [
        mock.Mock(id=101),
        mock.Mock(id=102),
        mock.Mock(id=103),
    ]
    mock_scan_stop.return_value = None
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli, ["scan", "--runtime=local", "stop", "--all"]
    )

    assert result.exception is None
    assert "Stopping 3 scan(s)" in result.output
    assert mock_scan_stop.call_count == 3
    mock_scan_stop.assert_any_call(scan_id=101)
    mock_scan_stop.assert_any_call(scan_id=102)
    mock_scan_stop.assert_any_call(scan_id=103)


@mock.patch.object(local_runtime.LocalRuntime, "list")
def testOstorlabScanStopCLI_whenStopAllIsUsedAndNoScansExist_showsWarning(
    mock_list_scans: mock.Mock, mocker: plugin.MockerFixture
) -> None:
    """Test ostorlab scan stop command with --all flag.
    Should show warning message when no scans are running.
    """

    mock_list_scans.return_value = []
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli, ["scan", "--runtime=local", "stop", "--all"]
    )

    assert result.exception is None
    assert "No running scans found" in result.output


@mock.patch.object(local_runtime.LocalRuntime, "stop")
@mock.patch.object(local_runtime.LocalRuntime, "list")
def testOstorlabScanStopCLI_whenStopAllWithShorthandIsUsedAndScansExist_stopsAllScans(
    mock_list_scans: mock.Mock, mock_scan_stop: mock.Mock, mocker: plugin.MockerFixture
) -> None:
    """Test ostorlab scan stop command with --all flag.
    Should stop all running scans.
    """

    mock_list_scans.return_value = [
        mock.Mock(id=101),
        mock.Mock(id=102),
        mock.Mock(id=103),
    ]
    mock_scan_stop.return_value = None
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    runner = CliRunner()

    result = runner.invoke(rootcli.rootcli, ["scan", "--runtime=local", "stop", "-a"])

    assert result.exception is None
    assert "Stopping 3 scan(s)" in result.output
    assert mock_scan_stop.call_count == 3
    mock_scan_stop.assert_any_call(scan_id=101)
    mock_scan_stop.assert_any_call(scan_id=102)
    mock_scan_stop.assert_any_call(scan_id=103)


@pytest.mark.parametrize(
    "progress_status",
    ["done", "stopped", "error"],
)
@mock.patch.object(local_runtime.LocalRuntime, "stop")
@mock.patch.object(local_runtime.LocalRuntime, "list")
def testOstorlabScanStopCLI_whenStopAllAndScansStatusNotInProgress_dontStop(
    mock_list_scans: mock.Mock,
    mock_scan_stop: mock.Mock,
    mocker: plugin.MockerFixture,
    progress_status: str,
) -> None:
    """Test ostorlab scan stop command with --all flag.
    Should not stop scans that are already done.
    """

    mock_list_scans.return_value = [
        mock.Mock(id=101, progress=progress_status),
        mock.Mock(id=102, progress=progress_status),
        mock.Mock(id=103, progress=progress_status),
    ]
    mock_scan_stop.return_value = None
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli, ["scan", "--runtime=local", "stop", "--all"]
    )

    assert result.exception is None
    assert mock_scan_stop.call_count == 0


@pytest.mark.parametrize(
    "progress_status",
    ["not_started", "in_progress"],
)
@mock.patch.object(local_runtime.LocalRuntime, "stop")
@mock.patch.object(local_runtime.LocalRuntime, "list")
def testOstorlabScanStopCLI_whenStopAllAndScansStatusInProgress_stopsScans(
    mock_list_scans: mock.Mock,
    mock_scan_stop: mock.Mock,
    mocker: plugin.MockerFixture,
    progress_status: str,
) -> None:
    """Test ostorlab scan stop command with --all flag.
    Should stop scans that are in progress or not started.
    """

    mock_list_scans.return_value = [
        mock.Mock(id=101, progress=progress_status),
        mock.Mock(id=102, progress=progress_status),
        mock.Mock(id=103, progress=progress_status),
    ]
    mock_scan_stop.return_value = None
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    runner = CliRunner()

    result = runner.invoke(
        rootcli.rootcli, ["scan", "--runtime=local", "stop", "--all"]
    )

    assert result.exception is None
    assert mock_scan_stop.call_count == 3
