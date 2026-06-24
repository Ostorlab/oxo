"""Unit test for the Client handler of the messaging queue."""

from typing import Any

import asyncio
from unittest import mock
from pytest_mock import plugin
import pytest

from ostorlab.scanner import handler as scanner_handler
from ostorlab.scanner import scanner_conf
from ostorlab.scanner.proto.scan._location import startAgentScan_pb2


@pytest.mark.nats
@pytest.mark.asyncio
async def testBusHandlerMessageParsing_whenPullingMessage_shouldParseAllAttributes(
    data_start_agent_scan: dict[str, Any],
    apk_start_agent_scan_bus_msg: startAgentScan_pb2.Message,
) -> None:
    """Ensure the pulling & parsing of the messages is performed correctly."""
    config = scanner_conf.ScannerConfig.from_json(config=data_start_agent_scan)
    bus_handler = scanner_handler.BusHandler(
        bus_url=config.bus_url,
        cluster_id=config.bus_cluster_id,
        name=config.bus_client_name,
    )
    await bus_handler._nc.connect()  # pylint: disable=W0212
    js = bus_handler._nc.jetstream()  # pylint: disable=W0212
    await js.publish(
        "scan.startAgentScan", apk_start_agent_scan_bus_msg.SerializeToString()
    )

    sub = await js.pull_subscribe("scan.startAgentScan", "durable_name")
    msgs = await sub.fetch(1)
    msg = msgs[0]

    parsed_request = await bus_handler.parse_message(msg)
    await msg.ack()

    assert parsed_request.reference_scan_id == 42
    assert parsed_request.key == "agentgroup/ostorlab/agent_group42"


def testClientBusHandler_shouldConnectWithUserCredentials(
    mocker: plugin.MockerFixture,
) -> None:
    """Test that user_credentials is passed correctly to nats.connect"""
    mock_connect = mocker.patch("nats.NATS.connect", new_callable=mock.AsyncMock)
    mocker.patch("nats.NATS.jetstream")

    bus_url = "nats://localhost:4222"
    cluster_id = "test-cluster"
    name = "test-client"
    nats_user_creds = "test-credentials"

    handler = scanner_handler.ClientBusHandler(
        bus_url=bus_url,
        cluster_id=cluster_id,
        name=name,
        nats_user_creds=nats_user_creds,
    )

    asyncio.run(handler.connect())

    mock_connect.assert_called_once()
    _, kwargs = mock_connect.call_args

    with open(kwargs.get("user_credentials"), "r") as f:
        assert f.read() == nats_user_creds
