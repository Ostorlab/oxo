"""Unit tests for scan handler module."""

import docker
import pytest
from pytest_mock import plugin

from ostorlab.scanner import scan_handler
from ostorlab.utils import scanner_state_reporter


@pytest.fixture(autouse=True)
def mock_firewall_setup(mocker: plugin.MockerFixture) -> None:
    """Mock firewall initialization by default so unit tests do not run host iptables."""
    mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.ensure_firewall_chains",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.flush_blacklist",
        return_value=True,
    )


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
        "_get_running_universes",
        side_effect=[set(), {"42"}],
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


def testGetRunningUniverses_whenServicesShareUniverses_returnsDistinctSet(
    mocker: plugin.MockerFixture,
) -> None:
    """_get_running_universes should return distinct universe IDs."""
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

    result = scan_handler_instance._get_running_universes()

    assert result == {"42", "43"}


def testGetRunningUniverses_whenDockerFails_returnsNone(
    mocker: plugin.MockerFixture,
) -> None:
    """_get_running_universes should return None on Docker error."""
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

    result = scan_handler_instance._get_running_universes()

    assert result is None


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
        "ostorlab.scanner.scan_handler.firewall.ensure_firewall_chains",
        return_value=True,
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
    assert scan_handler_instance._firewall_enabled is True
    assert scan_handler_instance._active_blacklists == {}


def testScanHandlerInit_whenEnsureChainsFails_recordsDisabledFirewall(
    mocker: plugin.MockerFixture,
) -> None:
    """ScanHandler.__init__ should record disabled firewall when setup fails."""
    mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.ensure_firewall_chains",
        return_value=False,
    )
    mock_flush = mocker.patch("ostorlab.scanner.scan_handler.firewall.flush_blacklist")
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )

    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    assert scan_handler_instance._firewall_enabled is False
    assert scan_handler_instance._firewall_healthy is True
    mock_flush.assert_called_once()


def testScanHandlerInit_whenEnsureChainsFailsAndFlushFails_stillRecordsDisabledFirewallAndHealthy(
    mocker: plugin.MockerFixture,
) -> None:
    """ScanHandler.__init__ should keep _firewall_healthy=True when disabled even if startup flush fails."""
    mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.ensure_firewall_chains",
        return_value=False,
    )
    mock_flush = mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.flush_blacklist",
        return_value=False,
    )
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )

    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    assert scan_handler_instance._firewall_enabled is False
    assert scan_handler_instance._firewall_healthy is True
    mock_flush.assert_called_once()


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
    mock_apply = mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.apply_blacklist",
        return_value=True,
    )
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
    assert scan_handler_instance._active_blacklists == {"42": ["1.2.3.4", "10.0.0.0/8"]}


def testTriggerScanWithRollback_whenFirewallDisabledAndBlacklistPresent_rollsBack(
    mocker: plugin.MockerFixture,
) -> None:
    """_trigger_scan_with_rollback rolls back when firewall is disabled and blacklist required."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._firewall_enabled = False
    mock_apply = mocker.patch("ostorlab.scanner.scan_handler.firewall.apply_blacklist")
    runner = mocker.MagicMock()
    runner.execute.return_value = {"data": {"updateScan": {"success": True}}}
    reserved_scan = {
        "id": 42,
        "blacklistedIps": ["1.2.3.4"],
    }

    result = scan_handler_instance._trigger_scan_with_rollback(
        runner=runner, reserved_scan=reserved_scan, api_key="test-key"
    )

    assert result is None
    mock_apply.assert_not_called()
    assert scan_handler_instance._active_blacklists == {}
    runner.execute.assert_called_once()


def testTriggerScanWithRollback_whenApplyBlacklistFails_rollsBack(
    mocker: plugin.MockerFixture,
) -> None:
    """_trigger_scan_with_rollback rolls back when apply_blacklist returns False."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.apply_blacklist",
        return_value=False,
    )
    runner = mocker.MagicMock()
    runner.execute.return_value = {"data": {"updateScan": {"success": True}}}
    reserved_scan = {
        "id": 42,
        "blacklistedIps": ["1.2.3.4"],
    }

    result = scan_handler_instance._trigger_scan_with_rollback(
        runner=runner, reserved_scan=reserved_scan, api_key="test-key"
    )

    assert result is None
    assert scan_handler_instance._active_blacklists == {}
    runner.execute.assert_called_once()


def testTriggerScanWithRollback_whenNoBlacklistAndOtherActiveRules_preservesActiveRules(
    mocker: plugin.MockerFixture,
) -> None:
    """_trigger_scan_with_rollback leaves existing rules untouched when new scan has no blacklist."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._active_blacklists = {"41": ["1.1.1.1"]}
    mock_apply = mocker.patch("ostorlab.scanner.scan_handler.firewall.apply_blacklist")
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
    mock_flush.assert_not_called()
    mock_apply.assert_not_called()
    assert scan_handler_instance._active_blacklists == {"41": ["1.1.1.1"]}


def testTriggerScanWithRollback_whenMultipleScansWithBlacklists_mergesUnion(
    mocker: plugin.MockerFixture,
) -> None:
    """_trigger_scan_with_rollback merges union of blacklisted IPs across concurrent scans."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._active_blacklists = {"41": ["1.1.1.1"]}
    mock_apply = mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.apply_blacklist",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.scanner.scan_handler.callbacks.start_scan",
        return_value="local-42",
    )
    runner = mocker.MagicMock()
    reserved_scan = {
        "id": 42,
        "blacklistedIps": ["2.2.2.2", "1.1.1.1"],
    }

    result = scan_handler_instance._trigger_scan_with_rollback(
        runner=runner, reserved_scan=reserved_scan, api_key="test-key"
    )

    assert result == "local-42"
    mock_apply.assert_called_once_with(["1.1.1.1", "2.2.2.2"])
    assert scan_handler_instance._active_blacklists == {
        "41": ["1.1.1.1"],
        "42": ["2.2.2.2", "1.1.1.1"],
    }


def testRollbackScanState_whenOtherActiveScansExist_resyncsRemainingRules(
    mocker: plugin.MockerFixture,
) -> None:
    """_rollback_scan_state removes failed scan from active blacklists and resyncs remaining."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._active_blacklists = {
        "41": ["1.1.1.1"],
        "42": ["2.2.2.2"],
    }
    mock_apply = mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.apply_blacklist",
        return_value=True,
    )
    runner = mocker.MagicMock()

    scan_handler_instance._rollback_scan_state(runner=runner, scan_id_val=42)

    mock_apply.assert_called_once_with(["1.1.1.1"])
    assert scan_handler_instance._active_blacklists == {"41": ["1.1.1.1"]}


def testRollbackScanState_whenLastActiveScanRollsBack_flushesBlacklist(
    mocker: plugin.MockerFixture,
) -> None:
    """_rollback_scan_state flushes blacklist when no other scans remain."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._active_blacklists = {"42": ["2.2.2.2"]}
    mock_flush = mocker.patch("ostorlab.scanner.scan_handler.firewall.flush_blacklist")
    runner = mocker.MagicMock()

    scan_handler_instance._rollback_scan_state(runner=runner, scan_id_val=42)

    mock_flush.assert_called_once()
    assert scan_handler_instance._active_blacklists == {}


def testTriggerScanWithRollback_whenStartScanFailsWithBlacklist_rollsBackAndResyncs(
    mocker: plugin.MockerFixture,
) -> None:
    """_trigger_scan_with_rollback should roll back and resync remaining on scan start failure."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._active_blacklists = {"41": ["1.1.1.1"]}
    mock_apply = mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.apply_blacklist",
        return_value=True,
    )
    mocker.patch(
        "ostorlab.scanner.scan_handler.callbacks.start_scan",
        side_effect=RuntimeError("start failed"),
    )
    runner = mocker.MagicMock()
    reserved_scan = {
        "id": 42,
        "blacklistedIps": ["2.2.2.2"],
    }

    result = scan_handler_instance._trigger_scan_with_rollback(
        runner=runner, reserved_scan=reserved_scan, api_key="test-key"
    )

    assert result is None
    assert mock_apply.call_args_list == [
        mocker.call(["1.1.1.1", "2.2.2.2"]),
        mocker.call(["1.1.1.1"]),
    ]
    assert scan_handler_instance._active_blacklists == {"41": ["1.1.1.1"]}


def testHandleMessages_whenOneUniverseFinishes_resyncsRemainingRules(
    mocker: plugin.MockerFixture,
) -> None:
    """handle_messages should resync firewall when one of multiple universes finishes."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._active_blacklists = {
        "41": ["1.1.1.1"],
        "42": ["2.2.2.2"],
    }
    mocker.patch.object(
        scan_handler_instance,
        "_get_running_universes",
        return_value={"42"},
    )
    mocker.patch(
        "ostorlab.scanner.scan_handler.time.sleep",
        side_effect=RuntimeError("stop"),
    )
    mock_apply = mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.apply_blacklist",
        return_value=True,
    )
    runner = mocker.MagicMock()

    with pytest.raises(RuntimeError, match="stop"):
        scan_handler_instance.handle_messages(runner=runner)

    mock_apply.assert_called_once_with(["2.2.2.2"])
    assert scan_handler_instance._active_blacklists == {"42": ["2.2.2.2"]}


def testHandleMessages_whenAllUniversesFinish_flushesBlacklist(
    mocker: plugin.MockerFixture,
) -> None:
    """handle_messages should flush blacklist when all running universes finish."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._active_blacklists = {"42": ["2.2.2.2"]}
    mocker.patch.object(
        scan_handler_instance,
        "_get_running_universes",
        return_value=set(),
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
    assert scan_handler_instance._active_blacklists == {}


def testClose_whenNoActiveBlacklists_flushesBlacklist(
    mocker: plugin.MockerFixture,
) -> None:
    """close should flush blacklist when no active blacklists remain."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._docker_client = mocker.MagicMock()
    scan_handler_instance._active_blacklists = {}
    mock_flush = mocker.patch("ostorlab.scanner.scan_handler.firewall.flush_blacklist")

    scan_handler_instance.close()

    mock_flush.assert_called_once()


def testClose_whenActiveBlacklistsRemain_resyncsRulesAndDoesNotFlush(
    mocker: plugin.MockerFixture,
) -> None:
    """close should resync rules when active blacklists remain for swarm services."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._docker_client = mocker.MagicMock()
    scan_handler_instance._active_blacklists = {"42": ["2.2.2.2"]}
    mock_flush = mocker.patch("ostorlab.scanner.scan_handler.firewall.flush_blacklist")
    mock_apply = mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.apply_blacklist",
        return_value=True,
    )

    scan_handler_instance.close()

    mock_flush.assert_not_called()
    mock_apply.assert_called_once_with(["2.2.2.2"])


def testSyncFirewallRules_whenFlushFailsOnEmptyBlacklist_returnsFalseAndMarksUnhealthy(
    mocker: plugin.MockerFixture,
) -> None:
    """_sync_firewall_rules should return False and mark firewall unhealthy if flush fails."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._active_blacklists = {}
    mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.flush_blacklist",
        return_value=False,
    )

    result = scan_handler_instance._sync_firewall_rules()

    assert result is False
    assert scan_handler_instance._firewall_healthy is False


def testRollbackScanState_whenSyncFails_returnsFalseAndMarksFirewallUnhealthy(
    mocker: plugin.MockerFixture,
) -> None:
    """_rollback_scan_state returns False and marks firewall unhealthy when sync fails."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._active_blacklists = {
        "41": ["1.1.1.1"],
        "42": ["2.2.2.2"],
    }
    mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.apply_blacklist",
        return_value=False,
    )
    runner = mocker.MagicMock()

    result = scan_handler_instance._rollback_scan_state(runner=runner, scan_id_val=42)

    assert result is False
    assert scan_handler_instance._firewall_healthy is False


def testHandleMessages_whenUniverseFinishesAndSyncFails_pausesAndDoesNotSchedule(
    mocker: plugin.MockerFixture,
) -> None:
    """handle_messages pauses scheduling and does not reserve scans when finished universe sync fails."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._active_blacklists = {
        "41": ["1.1.1.1"],
        "42": ["2.2.2.2"],
    }
    mocker.patch.object(
        scan_handler_instance,
        "_get_running_universes",
        return_value={"42"},
    )
    mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.apply_blacklist",
        return_value=False,
    )
    mock_fetch = mocker.patch.object(scan_handler_instance, "_fetch_available_scans")
    mocker.patch(
        "ostorlab.scanner.scan_handler.time.sleep",
        side_effect=RuntimeError("stop"),
    )
    runner = mocker.MagicMock()

    with pytest.raises(RuntimeError, match="stop"):
        scan_handler_instance.handle_messages(runner=runner)

    mock_fetch.assert_not_called()
    assert scan_handler_instance._firewall_healthy is False


def testHandleMessages_whenFirewallUnhealthy_retriesSyncAndSkipsSchedulingIfFailed(
    mocker: plugin.MockerFixture,
) -> None:
    """handle_messages retries sync when firewall unhealthy and pauses if it fails."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._firewall_healthy = False
    scan_handler_instance._active_blacklists = {"42": ["2.2.2.2"]}

    mocker.patch.object(
        scan_handler_instance,
        "_get_running_universes",
        return_value={"42"},
    )
    mock_sync = mocker.patch.object(
        scan_handler_instance,
        "_sync_firewall_rules",
        return_value=False,
    )
    mock_fetch = mocker.patch.object(scan_handler_instance, "_fetch_available_scans")
    mocker.patch(
        "ostorlab.scanner.scan_handler.time.sleep",
        side_effect=RuntimeError("stop"),
    )
    runner = mocker.MagicMock()

    with pytest.raises(RuntimeError, match="stop"):
        scan_handler_instance.handle_messages(runner=runner)

    mock_sync.assert_called_once()
    mock_fetch.assert_not_called()


def testSyncFirewallRules_whenFirewallDisabled_returnsTrue(
    mocker: plugin.MockerFixture,
) -> None:
    """_sync_firewall_rules should return True as no-op when firewall is disabled."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._firewall_enabled = False

    result = scan_handler_instance._sync_firewall_rules()

    assert result is True
    assert scan_handler_instance._firewall_healthy is True


def testHandleMessages_whenFirewallDisabled_schedulesScansNormally(
    mocker: plugin.MockerFixture,
) -> None:
    """handle_messages should not pause or get stuck in retry loop when firewall is disabled."""
    mocker.patch(
        "ostorlab.scanner.scan_handler.firewall.ensure_firewall_chains",
        return_value=False,
    )
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    runner = mocker.MagicMock()
    mocker.patch.object(
        scan_handler_instance,
        "_fetch_available_scans",
        return_value=[{"id": 1}],
    )
    mocker.patch.object(
        scan_handler_instance,
        "_reserve_single_scan",
        return_value={"id": 42},
    )
    mocker.patch.object(
        scan_handler_instance,
        "_get_running_universes",
        side_effect=[set(), {"42"}],
    )
    trigger_mock = mocker.patch.object(
        scan_handler_instance,
        "_trigger_scan_with_rollback",
        return_value=42,
    )
    mocker.patch("time.sleep", side_effect=RuntimeError("stop"))

    with pytest.raises(RuntimeError, match="stop"):
        scan_handler_instance.handle_messages(runner=runner)

    trigger_mock.assert_called_once()


def testClose_whenFirewallDisabled_doesNotFlush(
    mocker: plugin.MockerFixture,
) -> None:
    """close should not flush blacklist when firewall is disabled."""
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname="test-host",
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)
    scan_handler_instance._firewall_enabled = False
    mock_flush = mocker.patch("ostorlab.scanner.scan_handler.firewall.flush_blacklist")

    scan_handler_instance.close()

    mock_flush.assert_not_called()
