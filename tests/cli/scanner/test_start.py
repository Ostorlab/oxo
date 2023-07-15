"""Unittests for start module."""
import pytest

from ostorlab.cli.scanner import start
from ostorlab.cli.scanner import nats_conf
from ostorlab.apis.runners import authenticated_runner


@pytest.mark.asyncio
async def testConnectNats_whenScannerConfig_subscribeNats(
    requests_mock, mocker, event_loop, data_scan_saved
):
    nats_connect_mock = mocker.patch(
        "ostorlab.cli.scanner.handler.ClientBusHandler.connect"
    )
    mocker.patch(
        "ostorlab.cli.scanner.start.asyncio.events.AbstractEventLoop.run_forever",
        side_effect=Exception,
    )
    nats_add_stream_mock = mocker.patch(
        "ostorlab.cli.scanner.handler.ClientBusHandler.add_stream"
    )
    mocker.patch("ostorlab.cli.scanner.handler.BusHandler.subscribe")

    requests_mock.post(
        authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=data_scan_saved,
        status_code=200,
    )

    config = nats_conf.ScannerConfig.from_json(data_scan_saved)

    await start.connect_nats(config=config, scanner_id="GGBD-DJJD-DKJK-DJDD")

    assert nats_connect_mock.call_count == 1
    assert (
        nats_add_stream_mock.call_args.kwargs["subjects"][0] == "scan_engine.scan_done"
    )


@pytest.mark.asyncio
async def testConnectNats_whenScannerConfig_subscribeNatsWithStartAgentScan(
    requests_mock, mocker, event_loop, data_start_agent_scan
):
    nats_connect_mock = mocker.patch(
        "ostorlab.cli.scanner.handler.ClientBusHandler.connect"
    )
    mocker.patch(
        "ostorlab.cli.scanner.start.asyncio.events.AbstractEventLoop.run_forever",
        side_effect=Exception,
    )
    nats_add_stream_mock = mocker.patch(
        "ostorlab.cli.scanner.handler.ClientBusHandler.add_stream"
    )
    mocker.patch("ostorlab.cli.scanner.handler.BusHandler.subscribe")

    requests_mock.post(
        authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=data_start_agent_scan,
        status_code=200,
    )

    config = nats_conf.ScannerConfig.from_json(data_start_agent_scan)

    await start.connect_nats(config=config, scanner_id="GGBD-DJJD-DKJK-DJDD")

    assert nats_connect_mock.call_count == 1
    assert nats_add_stream_mock.call_args.kwargs["subjects"][0] == "scan.startAgentScan"


@pytest.mark.asyncio
async def testBusHandler_always_createBusHandler(mocker, data_start_agent_scan):
    nats_subscribe_mock = mocker.patch(
        "ostorlab.cli.scanner.handler.BusHandler.subscribe"
    )
    mocker.patch(
        "ostorlab.cli.scanner.handler.ClientBusHandler.connect", return_value=None
    )
    mocker.patch(
        "ostorlab.cli.scanner.handler.ClientBusHandler.publish", return_value=None
    )
    mocker.patch(
        "ostorlab.cli.scanner.handler.ClientBusHandler.close", return_value=None
    )
    mocker.patch(
        "ostorlab.cli.scanner.handler.ClientBusHandler.add_stream", return_value=None
    )
    config = nats_conf.ScannerConfig.from_json(data_start_agent_scan)
    scan_handler = start.ScanHandler()
    await scan_handler.subscribe_all(config)

    assert nats_subscribe_mock.call_count == 1
    assert nats_subscribe_mock.await_args.kwargs["subject"] == "scan.startAgentScan"
    assert nats_subscribe_mock.await_args.kwargs["queue"] == "1"
