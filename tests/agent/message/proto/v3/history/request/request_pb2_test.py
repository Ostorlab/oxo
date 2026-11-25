"""Unit tests for the history request protobuf message."""

from ostorlab.agent.message import message as agent_message
from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.history.request import request_pb2


def testMessageFromData_whenDomainNameWithAsks_roundTrips() -> None:
    data = {
        "domain_name": {"name": "monzo.com"},
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


def testMessageFromData_whenDomainName_setsTheDomainNameAsset() -> None:
    serialized = agent_message.Message.from_data(
        "v3.history.request",
        {"domain_name": {"name": "monzo.com"}, "asks": [{"type": "dns"}]},
    )

    message = serializer.deserialize("v3.history.request", serialized.raw)

    assert isinstance(message, request_pb2.Message)
    assert message.WhichOneof("asset") == "domain_name"
    assert message.domain_name.name == "monzo.com"
    assert message.asks[0].type == "dns"
    assert message.asks[0].HasField("start") is False


def testMessageFromData_whenIpv4WithMask_roundTrips() -> None:
    data = {
        "ipv4": {"host": "8.8.8.8", "mask": "32", "version": 4},
        "asks": [{"type": "certificates"}],
    }

    serialized = agent_message.Message.from_data("v3.history.request", data)
    deserialized = agent_message.Message.from_raw("v3.history.request", serialized.raw)
    message = serializer.deserialize("v3.history.request", serialized.raw)

    assert deserialized.data == data
    assert isinstance(message, request_pb2.Message)
    assert message.WhichOneof("asset") == "ipv4"
    assert message.HasField("domain_name") is False


def testMessageFromData_whenIpv6WithStart_roundTrips() -> None:
    data = {
        "ipv6": {"host": "2001:db8::1", "mask": "128", "version": 6},
        "asks": [{"type": "certificates", "start": "2026-10-30T00:00:00Z"}],
    }

    serialized = agent_message.Message.from_data("v3.history.request", data)
    deserialized = agent_message.Message.from_raw("v3.history.request", serialized.raw)
    message = serializer.deserialize("v3.history.request", serialized.raw)

    assert deserialized.data == data
    assert isinstance(message, request_pb2.Message)
    assert message.WhichOneof("asset") == "ipv6"
    assert message.asks[0].start == "2026-10-30T00:00:00Z"
