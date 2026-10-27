"""Unit tests for scan handler module."""

import json
from typing import Any

import docker
import pytest
from pytest_mock import plugin

from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import runtime as local_runtime
from ostorlab.runtimes.local import snapshot
from ostorlab.scanner import scan_handler
from ostorlab.utils import scanner_state_reporter


def testHandleMessages_whenApiKeyProvided_forwardsApiKeyToStartScan(
    mocker: plugin.MockerFixture,
) -> None:
    """handle_messages should forward the api_key to _trigger_scan_with_rollback
    so the image pull uses a short-lived registry token."""
    trigger_mock = mocker.patch.object(
        scan_handler.ScanHandler,
        "_trigger_scan_with_rollback",
        return_value="scan-id",
    )
    mocker.patch.object(
        scan_handler.ScanHandler,
        "_fetch_available_scans",
        return_value=[{"id": 1}],
    )
    mocker.patch.object(
        scan_handler.ScanHandler,
        "_reserve_single_scan",
        return_value={"id": 42, "agentGroup": {"key": "test/group"}},
    )
    mocker.patch.object(
        scan_handler.ScanHandler,
        "_count_running_universes",
        side_effect=[0, 1],
    )
    mocker.patch(
        "ostorlab.scanner.scan_handler.time.sleep",
        side_effect=RuntimeError("stop"),
    )

    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    runner = mocker.MagicMock()

    with pytest.raises(RuntimeError, match="stop"):
        scan_handler_instance.handle_messages(runner, api_key="test_api_key")

    trigger_mock.assert_called_once()
    assert trigger_mock.call_args.kwargs["api_key"] == "test_api_key"


def testCountRunningUniverses_whenServicesShareUniverses_countsDistinctValues(
    mocker: plugin.MockerFixture,
) -> None:
    """_count_running_universes should count distinct universes, not services."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    docker_client_mock = mocker.MagicMock()
    scan_handler_instance._docker_client = docker_client_mock
    docker_client_mock.services.list.return_value = [
        mocker.MagicMock(attrs={"Spec": {"Labels": {"ostorlab.universe": "42"}}}),
        mocker.MagicMock(attrs={"Spec": {"Labels": {"ostorlab.universe": "42"}}}),
        mocker.MagicMock(attrs={"Spec": {"Labels": {"ostorlab.universe": "43"}}}),
        mocker.MagicMock(attrs={"Spec": {"Labels": {}}}),
    ]

    result = scan_handler_instance._count_running_universes()

    assert result == 2


def testCountRunningUniverses_whenDockerFails_returnsLimitSoHostLooksFull(
    mocker: plugin.MockerFixture,
) -> None:
    """A Docker error must not let the host claim more scans."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(
        state_reporter=state_reporter, max_concurrent_scans=3
    )
    docker_client_mock = mocker.MagicMock()
    scan_handler_instance._docker_client = docker_client_mock
    docker_client_mock.services.list.side_effect = docker.errors.DockerException("boom")

    result = scan_handler_instance._count_running_universes()

    assert result == 3


def testReserveSingleScan_whenFirstScanSucceeds_returnsScanData(
    mocker: plugin.MockerFixture,
) -> None:
    """_reserve_single_scan should return scan data when the first reservation succeeds."""
    runner = mocker.MagicMock()
    runner.execute.return_value = {
        "data": {
            "updateScan": {
                "success": True,
                "scan": {"id": 42, "progress": "locked"},
            }
        }
    }
    scans_list = [{"id": 42}, {"id": 99}]

    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    result = scan_handler_instance._reserve_single_scan(runner, scans_list)

    assert result == {"id": 42, "progress": "locked"}
    runner.execute.assert_called_once()
    request_arg = runner.execute.call_args.kwargs["request"]
    assert request_arg._scanner_id == "GGBD-DJJD-DKJK-DJDD"


def testReserveSingleScan_whenReservationFails_skipsAndTriesNext(
    mocker: plugin.MockerFixture,
) -> None:
    """_reserve_single_scan should try the next scan when reservation fails."""
    mocker.patch("random.shuffle", return_value=None)

    runner = mocker.MagicMock()
    runner.execute.side_effect = [
        {
            "data": {
                "updateScan": {
                    "success": False,
                    "scan": None,
                }
            }
        },
        {
            "data": {
                "updateScan": {
                    "success": True,
                    "scan": {"id": 99, "progress": "locked"},
                }
            }
        },
    ]
    scans_list = [{"id": 42}, {"id": 99}]

    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    result = scan_handler_instance._reserve_single_scan(runner, scans_list)

    assert result == {"id": 99, "progress": "locked"}
    assert runner.execute.call_count == 2
    for call in runner.execute.call_args_list:
        assert call.kwargs["request"]._scanner_id == "GGBD-DJJD-DKJK-DJDD"


def testReserveSingleScan_whenAllFail_returnsNone(
    mocker: plugin.MockerFixture,
) -> None:
    """_reserve_single_scan should return None when all reservations fail."""
    runner = mocker.MagicMock()
    runner.execute.return_value = {
        "data": {
            "updateScan": {
                "success": False,
                "scan": None,
            }
        }
    }
    scans_list = [{"id": 42}, {"id": 99}]

    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    result = scan_handler_instance._reserve_single_scan(runner, scans_list)

    assert result is None


def testTriggerScanWithRollback_whenStartScanFails_rollsBack(
    mocker: plugin.MockerFixture,
) -> None:
    """_trigger_scan_with_rollback should rollback scan state when callbacks.start_scan raises."""
    runner = mocker.MagicMock()
    runner.execute.return_value = {"data": {"updateScan": {"success": True}}}
    mocker.patch(
        "ostorlab.scanner.scan_handler.callbacks.start_scan",
        side_effect=Exception("scan failed"),
    )
    reserved_scan = {"id": 42, "agentGroup": {"key": "test/group"}}

    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    result = scan_handler_instance._trigger_scan_with_rollback(
        runner, reserved_scan, api_key="test_key"
    )

    assert result is None
    assert runner.execute.call_count == 1
    call_arg = runner.execute.call_args.kwargs["request"]
    assert call_arg.__class__.__name__ == "ScanUpdateStateAPIRequest"


def _mock_reserved_scan(mocker: plugin.MockerFixture) -> Any:
    """Make the API return one scan, reserve it, then stop the polling loop on its next sleep."""
    docker_client = mocker.patch(
        "ostorlab.scanner.scan_handler.docker.from_env"
    ).return_value
    docker_client.services.list.side_effect = [
        [],
        [mocker.MagicMock(attrs={"Spec": {"Labels": {"ostorlab.universe": "42"}}})],
    ]
    mocker.patch(
        "ostorlab.scanner.scan_handler.time.sleep",
        side_effect=RuntimeError("stop"),
    )
    runner = mocker.MagicMock()
    runner.execute.side_effect = [
        {"data": {"scans": {"scans": [], "pageInfo": {"numPages": 1}}}},
        {"data": {"scans": {"scans": [{"id": 42}]}}},
        {
            "data": {
                "updateScan": {
                    "success": True,
                    "scan": {"id": 42, "agentGroup": {"key": "test/group"}},
                }
            }
        },
        {"data": {"updateScan": {"success": True}}},
    ]
    return runner


def testHandleMessages_whenSnapshotRestoreFails_reportsScanPaused(
    mocker: plugin.MockerFixture,
) -> None:
    """A scan that cannot resume from its snapshot goes back to paused instead of not_started."""
    runner = _mock_reserved_scan(mocker)
    mocker.patch(
        "ostorlab.scanner.scan_handler.callbacks.start_scan",
        side_effect=local_runtime.SnapshotRestoreError("broken snapshot"),
    )
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    with pytest.raises(RuntimeError, match="stop"):
        scan_handler_instance.handle_messages(runner, api_key="test_key")

    assert runner.execute.call_count == 4
    variables = json.loads(runner.execute.call_args.kwargs["request"].data["variables"])
    assert variables["scanId"] == 42
    assert variables["progress"] == "paused"


def testHandleMessages_whenSnapshotBucketCannotBeRead_reportsScanNotStarted(
    mocker: plugin.MockerFixture,
) -> None:
    """A bucket that cannot be read puts the scan back to not_started, another attempt looks its snapshot up again."""
    runner = _mock_reserved_scan(mocker)
    mocker.patch(
        "ostorlab.scanner.scan_handler.callbacks.start_scan",
        side_effect=snapshot.StorageError("bucket unreachable"),
    )
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    with pytest.raises(RuntimeError, match="stop"):
        scan_handler_instance.handle_messages(runner, api_key="test_key")

    assert runner.execute.call_count == 4
    variables = json.loads(runner.execute.call_args.kwargs["request"].data["variables"])
    assert variables["scanId"] == 42
    assert variables["progress"] == "not_started"


def testHandleMessages_whenSnapshotSettingsProvided_forwardsThemToStartScan(
    mocker: plugin.MockerFixture,
) -> None:
    """The scanner snapshot storage reaches the runtime of each scan."""
    runner = _mock_reserved_scan(mocker)
    settings = definitions.SnapshotSettings(
        bucket="scan-snapshots", service_account=b"{}"
    )
    start_scan_mock = mocker.patch(
        "ostorlab.scanner.scan_handler.callbacks.start_scan", return_value="42"
    )
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(
        state_reporter=state_reporter, snapshot_settings=settings
    )

    with pytest.raises(RuntimeError, match="stop"):
        scan_handler_instance.handle_messages(runner, api_key="test_key")

    start_scan_mock.assert_called_once()
    assert start_scan_mock.call_args.kwargs["snapshot_settings"] == settings


def testHandleMessages_whenGcpCredentialProvided_forwardsItToStartScan(
    mocker: plugin.MockerFixture,
) -> None:
    """Forward GCP logging credentials when starting a reserved scan."""
    docker_client = mocker.patch(
        "ostorlab.scanner.scan_handler.docker.from_env"
    ).return_value
    docker_client.services.list.side_effect = [
        [],
        [mocker.MagicMock(attrs={"Spec": {"Labels": {"ostorlab.universe": "42"}}})],
    ]
    start_scan_mock = mocker.patch(
        "ostorlab.scanner.scan_handler.callbacks.start_scan", return_value="42"
    )
    mocker.patch(
        "ostorlab.scanner.scan_handler.time.sleep",
        side_effect=RuntimeError("stop"),
    )
    runner = mocker.MagicMock()
    runner.execute.side_effect = [
        {"data": {"scans": {"scans": [], "pageInfo": {"numPages": 1}}}},
        {"data": {"scans": {"scans": [{"id": 42}]}}},
        {
            "data": {
                "updateScan": {
                    "success": True,
                    "scan": {"id": 42, "agentGroup": {"key": "test/group"}},
                }
            }
        },
    ]
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(
        state_reporter=state_reporter,
        gcp_logging_credential="gcp-credential",
    )

    with pytest.raises(RuntimeError, match="stop"):
        scan_handler_instance.handle_messages(runner, api_key="test-key")

    start_scan_mock.assert_called_once_with(
        request={"id": 42, "agentGroup": {"key": "test/group"}},
        state_reporter=state_reporter,
        api_key="test-key",
        gcp_logging_credential="gcp-credential",
        snapshot_settings=None,
    )


def testReserveSingleScan_whenEntryHasNoId_skipsEntry(
    mocker: plugin.MockerFixture,
) -> None:
    """_reserve_single_scan should skip entries with no id."""
    runner = mocker.MagicMock()
    runner.execute.return_value = {
        "data": {
            "updateScan": {
                "success": True,
                "scan": {"id": 99, "progress": "locked"},
            }
        }
    }
    scans_list: list[dict[str, Any]] = [{"no_id": True}, {"id": 99}]

    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    result = scan_handler_instance._reserve_single_scan(runner, scans_list)

    assert result == {"id": 99, "progress": "locked"}
    runner.execute.assert_called_once()


def testHandleMessages_whenAtCapacity_reconcilesFailedQueuesBeforeSleeping(
    mocker: plugin.MockerFixture,
) -> None:
    """An occupied scanner must still report a terminal worker processing failure."""
    docker_client = mocker.MagicMock()
    worker = mocker.MagicMock()
    worker.attrs = {
        "Spec": {
            "Labels": {"ostorlab.universe": "42", "ostorlab.queue_name": "worker"},
            "Mode": {"Replicated": {"Replicas": 1}},
            "TaskTemplate": {
                "RestartPolicy": {"Condition": "any"},
                "ContainerSpec": {"Labels": {"ostorlab.scan_id": "42"}},
            },
        }
    }
    worker.tasks.return_value = [{"Status": {"State": "running"}}]
    broker = mocker.MagicMock()
    broker.attrs = {"Spec": {"Labels": {"ostorlab.universe": "42", "ostorlab.mq": ""}}}
    broker.tasks.return_value = [
        {"Status": {"State": "running", "ContainerStatus": {"ContainerID": "mq"}}}
    ]
    docker_client.services.list.return_value = [worker, broker]
    docker_client.containers.get.return_value.exec_run.return_value = mocker.Mock(
        exit_code=0,
        output=b'[{"name":"worker_queue.failed","messages_ready":1,"messages_unacknowledged":0,"consumers":0}]',
    )
    mocker.patch("docker.from_env", return_value=docker_client)
    mocker.patch("time.sleep", side_effect=RuntimeError("stop"))
    reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="scanner", hostname="test", ip="127.0.0.1"
    )
    handler = scan_handler.ScanHandler(reporter, max_concurrent_scans=1)
    runner = mocker.MagicMock()
    runner.execute.side_effect = [
        {"data": {"scans": {"scans": [{"id": "42"}], "pageInfo": {"numPages": 1}}}},
        {"data": {"scans": {"scans": [{"id": "42"}], "pageInfo": {"numPages": 1}}}},
        {"data": {"updateScan": {"success": True}}},
    ]

    with pytest.raises(RuntimeError, match="stop"):
        handler.handle_messages(runner)

    assert (
        json.loads(runner.execute.call_args.kwargs["request"].data["variables"])[
            "progress"
        ]
        == "error"
    )
    worker.update.assert_not_called()
    broker.remove.assert_not_called()
