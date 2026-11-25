"""Unit tests for the history request protobuf message."""

from ostorlab.agent.message import message as agent_message
from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.history.request import request_pb2


def testMessageFromData_whenDomainNameWithAsks_roundTrips() -> None:
    data = {
        "domain_name": "monzo.com",
        "asks": [
            {"type": "certificates", "start": "2026-10-30T00:00:00Z"},
            {"type": "dns"},
            {"type": "screenshot", "start": "2026-09-01T00:00:00Z"},
        ],
    }

    serialized = agent_message.Message.from_data("v3.history.request", data)
    deserialized = agent_message.Message.from_raw("v3.history.request", serialized.raw)

    assert deserialized.selector == "v3.history.request"
    assert deserialized.data == data


def testMessageFromData_whenIp_roundTripsWithoutDomainName() -> None:
    serialized = agent_message.Message.from_data(
        "v3.history.request",
        {"ip": "2001:db8::1", "asks": [{"type": "certificates"}]},
    )

    message = serializer.deserialize("v3.history.request", serialized.raw)

    assert isinstance(message, request_pb2.Message)
    assert message.ip == "2001:db8::1"
    assert message.HasField("domain_name") is False
    assert len(message.asks) == 1
    assert message.asks[0].type == "certificates"
    assert message.asks[0].HasField("start") is False


def testMessageFromData_whenAskHasStart_keepsIt() -> None:
    serialized = agent_message.Message.from_data(
        "v3.history.request",
        {
            "ip": "203.0.113.7",
            "asks": [{"type": "certificates", "start": "2026-10-30T00:00:00Z"}],
        },
    )

    message = serializer.deserialize("v3.history.request", serialized.raw)

    assert isinstance(message, request_pb2.Message)
    assert message.ip == "203.0.113.7"
    assert message.asks[0].HasField("start") is True
    assert message.asks[0].start == "2026-10-30T00:00:00Z"
