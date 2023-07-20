"""Unittests for start module."""
import pytest

from ostorlab.scanner import start
from ostorlab.scanner import nats_conf
from ostorlab.apis.runners import authenticated_runner
from ostorlab.utils import scanner_state_reporter


@pytest.mark.asyncio
async def testConnectNats_whenScannerConfig_subscribeNatsWithStartAgentScan(
    requests_mock, mocker, data_start_agent_scan
):
    nats_connect_mock = mocker.patch(
        "ostorlab.scanner.handler.ClientBusHandler.connect"
    )
    mocker.patch(
        "ostorlab.scanner.start.asyncio.events.AbstractEventLoop.run_forever",
        side_effect=Exception,
    )
    nats_add_stream_mock = mocker.patch(
        "ostorlab.scanner.handler.ClientBusHandler.add_stream"
    )
    mocker.patch("ostorlab.scanner.handler.BusHandler.subscribe")

    requests_mock.post(
        authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=data_start_agent_scan,
        status_code=200,
    )

    config = nats_conf.ScannerConfig.from_json(data_start_agent_scan)

    state_report = scanner_state_reporter.ScannerStateReporter(
        scanner_id="GGBD-DJJD-DKJK-DJDD", hostname=socket.gethostname(), ip="192.168.0.1"
    )
    await start.connect_nats(config=config, scanner_id="GGBD-DJJD-DKJK-DJDD", state_report=state_report)

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
    config = nats_conf.ScannerConfig.from_json(data_start_agent_scan)
    scan_handler = start.ScanHandler()

    await scan_handler.subscribe_all(config)

    assert nats_subscribe_mock.call_count == 1
    assert nats_subscribe_mock.await_args.kwargs["subject"] == "scan.startAgentScan"
    assert nats_subscribe_mock.await_args.kwargs["queue"] == "1"
