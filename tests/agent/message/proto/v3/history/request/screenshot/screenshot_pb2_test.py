"""Unit tests for the screenshot history request protobuf message."""

import pytest

from ostorlab.agent.message import message as agent_message
from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.history.request.screenshot import screenshot_pb2


def testMessageFromData_whenDomainNameWithStart_roundTrips() -> None:
    data = {"domain_name": {"name": "monzo.com"}, "start": "2026-10-30T00:00:00Z"}

    serialized = agent_message.Message.from_data("v3.history.request.screenshot", data)
    deserialized = agent_message.Message.from_raw(
        "v3.history.request.screenshot", serialized.raw
    )

    assert deserialized.selector == "v3.history.request.screenshot"
    assert deserialized.data == data


def testMessageFromData_whenDomainNameWithoutStart_keepsStartUnset() -> None:
    serialized = agent_message.Message.from_data(
        "v3.history.request.screenshot", {"domain_name": {"name": "monzo.com"}}
    )

    message = serializer.deserialize("v3.history.request.screenshot", serialized.raw)

    assert isinstance(message, screenshot_pb2.Message)
    assert message.WhichOneof("asset") == "domain_name"
    assert message.domain_name.name == "monzo.com"
    assert message.HasField("start") is False


def testMessage_hasNoIpField() -> None:
    assert [field.name for field in screenshot_pb2.Message.DESCRIPTOR.fields] == [
        "domain_name",
        "start",
    ]


@pytest.mark.parametrize(
    "asset",
    [
        {"ipv4": {"host": "1.1.1.1", "mask": "32", "version": 4}},
        {"ipv6": {"host": "2606:4700:4700::1111", "mask": "128", "version": 6}},
    ],
)
def testMessageFromData_whenIp_shouldRaiseSerializationError(
    asset: dict[str, dict[str, str | int]],
) -> None:
    with pytest.raises(serializer.SerializationError):
        agent_message.Message.from_data("v3.history.request.screenshot", asset)
