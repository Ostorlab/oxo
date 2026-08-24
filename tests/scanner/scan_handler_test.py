"""Unit tests for scan handler module."""

import pytest
from pytest_mock import plugin

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
        "_is_scan_running",
        return_value=True,
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


def testIsScanRunning_whenScanIdIsNone_returnsFalse() -> None:
    """_is_scan_running should return False when scan_id is None."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    result = scan_handler_instance._is_scan_running(scan_id=None)

    assert result is False


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
    mocker.patch.object(
        scan_handler,
        "random",
    )
    scan_handler.random.shuffle = lambda x: None

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
    """_trigger_scan_with_rollback should cleanup services and rollback when callbacks.start_scan raises."""
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_user_permitted", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_swarm_initialized",
        return_value=True,
    )
    docker_client = mocker.MagicMock()
    mocker.patch("docker.from_env", return_value=docker_client)
    service_mock = mocker.MagicMock()
    service_mock.attrs = {"Spec": {"Labels": {"ostorlab.universe": "42"}}}
    docker_client.services.list.return_value = [service_mock]
    docker_client.networks.list.return_value = []
    docker_client.configs.list.return_value = []
    docker_client.volumes.list.return_value = []

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
    service_mock.remove.assert_called_once()
    assert runner.execute.call_count == 1
    call_arg = runner.execute.call_args.kwargs["request"]
    assert call_arg.__class__.__name__ == "ScanUpdateStateAPIRequest"


def testCleanupScanServices_always_callsRuntimeCleanup(
    mocker: plugin.MockerFixture,
) -> None:
    """_cleanup_scan_services removes Docker services, networks, configs, and volumes for scan_id."""
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_user_permitted", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_docker_working", return_value=True
    )
    mocker.patch(
        "ostorlab.cli.docker_requirements_checker.is_swarm_initialized",
        return_value=True,
    )
    docker_client = mocker.MagicMock()
    mocker.patch("docker.from_env", return_value=docker_client)
    service_mock = mocker.MagicMock()
    service_mock.attrs = {"Spec": {"Labels": {"ostorlab.universe": "42"}}}
    docker_client.services.list.return_value = [service_mock]

    network_mock = mocker.MagicMock()
    network_mock.attrs = {"Labels": {"ostorlab.universe": "42"}}
    docker_client.networks.list.return_value = [network_mock]

    config_mock = mocker.MagicMock()
    config_mock.attrs = {"Spec": {"Labels": {"ostorlab.universe": "42"}}}
    docker_client.configs.list.return_value = [config_mock]

    volume_mock = mocker.MagicMock()
    volume_mock.attrs = {"Labels": {"ostorlab.universe": "42"}}
    docker_client.volumes.list.return_value = [volume_mock]

    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._cleanup_scan_services(scan_id="42")

    service_mock.remove.assert_called_once()
    network_mock.remove.assert_called_once()
    config_mock.remove.assert_called_once()
    volume_mock.remove.assert_called_once_with(force=True)


def testHandleMessages_whenGcpCredentialProvided_forwardsItToStartScan(
    mocker: plugin.MockerFixture,
) -> None:
    """Forward GCP logging credentials when starting a reserved scan."""
    docker_client = mocker.patch(
        "ostorlab.scanner.scan_handler.docker.from_env"
    ).return_value
    docker_client.services.list.return_value = [mocker.MagicMock()]
    start_scan_mock = mocker.patch(
        "ostorlab.scanner.scan_handler.callbacks.start_scan", return_value="42"
    )
    mocker.patch(
        "ostorlab.scanner.scan_handler.time.sleep",
        side_effect=RuntimeError("stop"),
    )
    runner = mocker.MagicMock()
    runner.execute.side_effect = [
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
    scans_list = [{"no_id": True}, {"id": 99}]

    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    result = scan_handler_instance._reserve_single_scan(runner, scans_list)

    assert result == {"id": 99, "progress": "locked"}
    runner.execute.assert_called_once()
