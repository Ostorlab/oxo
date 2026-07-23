"""Unit tests for scan handler module."""

import pytest
from pytest_mock import plugin

from ostorlab.scanner import scan_handler
from ostorlab.utils import scanner_state_reporter


@pytest.mark.asyncio
async def testHandleMessages_whenApiKeyProvided_forwardsApiKeyToStartScan(
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
        "ostorlab.scanner.scan_handler.asyncio.sleep",
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
        await scan_handler_instance.handle_messages(runner, api_key="test_api_key")

    trigger_mock.assert_called_once()
    assert trigger_mock.call_args.args[2] == "test_api_key"
