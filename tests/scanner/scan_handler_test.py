"""Unit tests for start module."""

import socket

import pytest

from ostorlab.scanner import scan_handler
from ostorlab.scanner import scanner_conf
from ostorlab.utils import scanner_state_reporter


@pytest.mark.asyncio
async def testConnectNats_whenScannerConfig_subscribeNatsWithStartAgentScan(
    mocker, data_start_agent_scan
):
    nats_connect_mock = mocker.patch(
        "ostorlab.scanner.handler.ClientBusHandler.connect"
    )
    mocker.patch(
        "ostorlab.scanner.scan_handler.asyncio.events.AbstractEventLoop.run_forever",
        side_effect=Exception,
    )
    nats_add_stream_mock = mocker.patch(
        "ostorlab.scanner.handler.ClientBusHandler.add_stream"
    )
    mocker.patch("ostorlab.scanner.handler.BusHandler.subscribe")
    mocker.patch("ostorlab.scanner.scan_handler.ScanHandler.handle_messages")
    mocker.patch("docker.from_env")

    config = scanner_conf.ScannerConfig.from_json(config=data_start_agent_scan)

    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname=socket.gethostname(),
        ip="192.168.0.1",
    )
    await scan_handler.connect_nats(
        config=config, scanner_id="GGBD-DJJD-DKJK-DJDD", state_reporter=state_reporter
    )

    assert nats_connect_mock.call_count == 1
    assert nats_add_stream_mock.call_args.kwargs["subjects"][0] == "scan.startAgentScan"


@pytest.mark.asyncio
async def testBusHandler_always_createBusHandler(mocker, data_start_agent_scan):
    nats_subscribe_mock = mocker.patch("ostorlab.scanner.handler.BusHandler.subscribe")
    mocker.patch("ostorlab.scanner.handler.ClientBusHandler.connect", return_value=None)
    mocker.patch("ostorlab.scanner.handler.ClientBusHandler.close", return_value=None)
    mocker.patch(
        "ostorlab.scanner.handler.ClientBusHandler.add_stream", return_value=None
    )
    mocker.patch("ostorlab.scanner.scan_handler.ScanHandler.handle_messages")
    config = scanner_conf.ScannerConfig.from_json(
        config=data_start_agent_scan,
    )
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname=socket.gethostname(),
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    await scan_handler_instance.subscribe_all(config)

    assert nats_subscribe_mock.call_count == 1
    assert nats_subscribe_mock.await_args.kwargs["subject"] == "scan.startAgentScan"
    assert nats_subscribe_mock.await_args.kwargs["durable_name"] == "1"


@pytest.mark.asyncio
async def testSubscribeAll_whenApiKeyProvided_forwardsApiKeyToHandleMessages(
    mocker, data_start_agent_scan
):
    """subscribe_all should propagate api_key to handle_messages so it can
    be passed all the way down to install_agent."""
    mocker.patch("ostorlab.scanner.handler.BusHandler.subscribe")
    mocker.patch("ostorlab.scanner.handler.ClientBusHandler.connect", return_value=None)
    mocker.patch("ostorlab.scanner.handler.ClientBusHandler.close", return_value=None)
    mocker.patch(
        "ostorlab.scanner.handler.ClientBusHandler.add_stream", return_value=None
    )
    handle_messages_mock = mocker.patch(
        "ostorlab.scanner.scan_handler.ScanHandler.handle_messages"
    )
    config = scanner_conf.ScannerConfig.from_json(config=data_start_agent_scan)
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname=socket.gethostname(),
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    await scan_handler_instance.subscribe_all(config, api_key="test_api_key")

    assert handle_messages_mock.call_count == 1
    assert handle_messages_mock.await_args.args[-1] == "test_api_key"


@pytest.mark.asyncio
async def testHandleMessages_whenApiKeyProvided_forwardsApiKeyToStartScan(
    mocker, data_start_agent_scan
):
    """handle_messages should forward the api_key to callbacks.start_scan
    so the image pull uses a short-lived registry token."""
    start_scan_mock = mocker.patch(
        "ostorlab.scanner.scan_handler.callbacks.start_scan", return_value="scan-id"
    )
    mocker.patch(
        "ostorlab.scanner.scan_handler._is_scan_running", side_effect=[False, True]
    )
    mocker.patch(
        "ostorlab.scanner.scan_handler.asyncio.sleep", side_effect=RuntimeError("stop")
    )

    async def _fake_process_message():
        msg = mocker.AsyncMock()
        yield msg, mocker.MagicMock()

    bus_handler = mocker.MagicMock()
    bus_handler.process_message = _fake_process_message

    config = scanner_conf.ScannerConfig.from_json(config=data_start_agent_scan)
    state_reporter = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD",
        hostname=socket.gethostname(),
        ip="192.168.0.1",
    )
    scan_handler_instance = scan_handler.ScanHandler(state_reporter=state_reporter)

    with pytest.raises(RuntimeError, match="stop"):
        await scan_handler_instance.handle_messages(
            bus_handler, config, api_key="test_api_key"
        )

    start_scan_mock.assert_called_once()
    assert start_scan_mock.call_args.kwargs.get("api_key") == "test_api_key"
