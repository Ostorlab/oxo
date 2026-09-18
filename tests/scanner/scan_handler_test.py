"""Unit tests for scan handler module."""

import docker
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
    scan_handler_instance._docker_client = mocker.MagicMock()
    scan_handler_instance._docker_client.services.list.return_value = [
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
    scan_handler_instance._docker_client = mocker.MagicMock()
    scan_handler_instance._docker_client.services.list.side_effect = (
        docker.errors.DockerException("boom")
    )

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


def testScanHandlerInit_always_ensuresFirewallChainsAndFlushesBlacklist(
    mocker: plugin.MockerFixture,
) -> None:
    """ScanHandler.__init__ should ensure firewall chains exist and flush blacklist."""
    mock_ensure = mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.ensure_firewall_chains"
    )
    mock_flush = mocker.patch("ostorlab.scanner.scan_handler.firewall.flush_blacklist")
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )

    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    mock_ensure.assert_called_once()
    mock_flush.assert_called_once()
    assert scan_handler_instance._has_active_firewall_rules is False


def testTriggerScanWithRollback_whenBlacklistedIpsPresent_appliesBlacklist(
    mocker: plugin.MockerFixture,
) -> None:
    """_trigger_scan_with_rollback applies blacklist when blacklistedIps present."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    mock_apply = mocker.patch("ostorlab.scanner.scan_handler.firewall.apply_blacklist")
    mocker.patch(
        "ostorlab.scanner.scan_handler.callbacks.start_scan",
        return_value="local-42",
    )
    runner = mocker.MagicMock()
    reserved_scan = {
        "id": 42,
        "blacklistedIps": ["1.2.3.4", "10.0.0.0/8"],
    }

    result = scan_handler_instance._trigger_scan_with_rollback(
        runner=runner, reserved_scan=reserved_scan, api_key="test-key"
    )

    assert result == "local-42"
    mock_apply.assert_called_once_with(["1.2.3.4", "10.0.0.0/8"])
    assert scan_handler_instance._has_active_firewall_rules is True


def testTriggerScanWithRollback_whenBlacklistEmptyAndRulesActive_flushesBlacklist(
    mocker: plugin.MockerFixture,
) -> None:
    """_trigger_scan_with_rollback flushes blacklist when empty but rules active."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._has_active_firewall_rules = True
    mock_flush = mocker.patch("ostorlab.scanner.scan_handler.firewall.flush_blacklist")
    mocker.patch(
        "ostorlab.scanner.scan_handler.callbacks.start_scan",
        return_value="local-42",
    )
    runner = mocker.MagicMock()

    result = scan_handler_instance._trigger_scan_with_rollback(
        runner=runner,
        reserved_scan={"id": 42, "blacklistedIps": []},
        api_key="test-key",
    )

    assert result == "local-42"
    mock_flush.assert_called_once()
    assert scan_handler_instance._has_active_firewall_rules is False


def testTriggerScanWithRollback_whenNoBlacklistAndNoActiveRules_doesNotTouchFirewall(
    mocker: plugin.MockerFixture,
) -> None:
    """_trigger_scan_with_rollback skips firewall when no IPs and no active rules."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    mock_apply = mocker.patch("ostorlab.scanner.scan_handler.firewall.apply_blacklist")
    mock_flush = mocker.patch("ostorlab.scanner.scan_handler.firewall.flush_blacklist")
    mocker.patch(
        "ostorlab.scanner.scan_handler.callbacks.start_scan",
        return_value="local-42",
    )

    result = scan_handler_instance._trigger_scan_with_rollback(
        runner=mocker.MagicMock(),
        reserved_scan={"id": 42},
        api_key="test-key",
    )

    assert result == "local-42"
    mock_apply.assert_not_called()
    mock_flush.assert_not_called()
    assert scan_handler_instance._has_active_firewall_rules is False


def testRollbackScanState_always_flushesBlacklistAndResetsFlag(
    mocker: plugin.MockerFixture,
) -> None:
    """_rollback_scan_state should flush blacklist and reset active flag."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._has_active_firewall_rules = True
    mock_flush = mocker.patch("ostorlab.scanner.scan_handler.firewall.flush_blacklist")
    runner = mocker.MagicMock()

    scan_handler_instance._rollback_scan_state(runner=runner, scan_id_val=42)

    mock_flush.assert_called_once()
    assert scan_handler_instance._has_active_firewall_rules is False


def testTriggerScanWithRollback_whenStartScanFailsWithBlacklist_flushesBlacklist(
    mocker: plugin.MockerFixture,
) -> None:
    """_trigger_scan_with_rollback should flush blacklist on scan start failure."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    mock_apply = mocker.patch("ostorlab.scanner.scan_handler.firewall.apply_blacklist")
    mock_flush = mocker.patch("ostorlab.scanner.scan_handler.firewall.flush_blacklist")
    mocker.patch(
        "ostorlab.scanner.scan_handler.callbacks.start_scan",
        side_effect=RuntimeError("start failed"),
    )
    runner = mocker.MagicMock()
    reserved_scan = {
        "id": 42,
        "blacklistedIps": ["1.2.3.4"],
    }

    result = scan_handler_instance._trigger_scan_with_rollback(
        runner=runner, reserved_scan=reserved_scan, api_key="test-key"
    )

    assert result is None
    mock_apply.assert_called_once_with(["1.2.3.4"])
    mock_flush.assert_called_once()
    assert scan_handler_instance._has_active_firewall_rules is False


def testHandleMessages_whenRunningUniverseFinishesAndHadActiveRules_flushesBlacklist(
    mocker: plugin.MockerFixture,
) -> None:
    """handle_messages should flush blacklist when running universe count drops to 0."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._has_active_firewall_rules = True
    mocker.patch.object(
        scan_handler.ScanHandler,
        "_count_running_universes",
        return_value=0,
    )
    mocker.patch(
        "ostorlab.scanner.scan_handler.time.sleep",
        side_effect=RuntimeError("stop"),
    )
    mock_flush = mocker.patch("ostorlab.scanner.scan_handler.firewall.flush_blacklist")
    runner = mocker.MagicMock()

    with pytest.raises(RuntimeError, match="stop"):
        scan_handler_instance.handle_messages(runner=runner)

    mock_flush.assert_called_once()
    assert scan_handler_instance._has_active_firewall_rules is False


def testClose_always_flushesBlacklistAndResetsFlag(
    mocker: plugin.MockerFixture,
) -> None:
    """close should flush blacklist and reset active flag."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._docker_client = mocker.MagicMock()
    scan_handler_instance._has_active_firewall_rules = True
    mock_flush = mocker.patch("ostorlab.scanner.scan_handler.firewall.flush_blacklist")

    scan_handler_instance.close()

    mock_flush.assert_called_once()
    assert scan_handler_instance._has_active_firewall_rules is False
