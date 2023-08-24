"""Unit test for the Client handler of the messaging queue."""
from typing import Dict, Any

import pytest

from ostorlab.scanner import handler as scanner_handler
from ostorlab.scanner import scanner_conf
from ostorlab.scanner.proto.scan._location import startAgentScan_pb2


@pytest.mark.skip(reason="NATS is not available in github workflow.")
@pytest.mark.asyncio
async def testBusHandlerMessageParsing_whenPullingMessage_shouldParseAllAttributes(
    data_start_agent_scan: Dict[str, Any],
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
