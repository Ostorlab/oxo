"""Unit tests for the certificate history request protobuf message."""

from ostorlab.agent.message import message as agent_message
from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.history.request.certificates import (
    certificates_pb2,
)


def testMessageFromData_whenDomainNameWithStart_roundTrips() -> None:
    data = {"domain_name": {"name": "monzo.com"}, "start": "2026-10-30T00:00:00Z"}

    serialized = agent_message.Message.from_data(
        "v3.history.request.certificates", data
    )
    deserialized = agent_message.Message.from_raw(
        "v3.history.request.certificates", serialized.raw
    )

    assert deserialized.selector == "v3.history.request.certificates"
    assert deserialized.data == data


def testMessageFromData_whenDomainNameWithoutStart_keepsStartUnset() -> None:
    serialized = agent_message.Message.from_data(
        "v3.history.request.certificates", {"domain_name": {"name": "monzo.com"}}
    )

    message = serializer.deserialize("v3.history.request.certificates", serialized.raw)

    assert isinstance(message, certificates_pb2.Message)
    assert message.WhichOneof("asset") == "domain_name"
    assert message.domain_name.name == "monzo.com"
    assert message.HasField("start") is False


def testMessageFromData_whenIpv4WithMask_roundTrips() -> None:
    data = {"ipv4": {"host": "1.1.1.1", "mask": "32", "version": 4}}

    serialized = agent_message.Message.from_data(
        "v3.history.request.certificates", data
    )
    deserialized = agent_message.Message.from_raw(
        "v3.history.request.certificates", serialized.raw
    )
    message = serializer.deserialize("v3.history.request.certificates", serialized.raw)

    assert deserialized.data == data
    assert isinstance(message, certificates_pb2.Message)
    assert message.WhichOneof("asset") == "ipv4"


def testMessageFromData_whenIpv6WithStart_roundTrips() -> None:
    data = {
        "ipv6": {"host": "2606:4700:4700::1111", "mask": "128", "version": 6},
        "start": "2026-10-30T00:00:00Z",
    }

    serialized = agent_message.Message.from_data(
        "v3.history.request.certificates", data
    )
    deserialized = agent_message.Message.from_raw(
        "v3.history.request.certificates", serialized.raw
    )
    message = serializer.deserialize("v3.history.request.certificates", serialized.raw)

    assert deserialized.data == data
    assert isinstance(message, certificates_pb2.Message)
    assert message.WhichOneof("asset") == "ipv6"
