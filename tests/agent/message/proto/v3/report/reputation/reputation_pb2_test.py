"""Unit tests for the reputation protobuf message."""

import pytest
from google.protobuf import message as protobuf_message

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.report.reputation import reputation_pb2


def testSerialize_whenDomainNameListed_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.report.reputation",
        {
            "domain_name": {"name": "example.com"},
            "source": "google_safe_browsing",
            "listed": True,
            "categories": ["MALWARE", "SOCIAL_ENGINEERING"],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.report.reputation", raw)

    assert isinstance(message, reputation_pb2.Message)
    assert message.WhichOneof("asset") == "domain_name"
    assert message.domain_name.name == "example.com"
    assert message.source == "google_safe_browsing"
    assert message.listed is True
    assert list(message.categories) == ["MALWARE", "SOCIAL_ENGINEERING"]


def testSerialize_whenDomainNameNotListed_shouldKeepTheVerdict() -> None:
    raw = serializer.serialize(
        "v3.report.reputation",
        {
            "domain_name": {"name": "example.com"},
            "source": "spamhaus_dbl",
            "listed": False,
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.report.reputation", raw)

    assert isinstance(message, reputation_pb2.Message)
    assert message.HasField("listed") is True
    assert message.listed is False
    assert list(message.categories) == []


def testSerialize_whenIpListed_shouldSetTheIpAsset() -> None:
    raw = serializer.serialize(
        "v3.report.reputation",
        {
            "ipv4": {"host": "192.0.2.1", "version": 4},
            "source": "abuseipdb",
            "listed": True,
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.report.reputation", raw)

    assert isinstance(message, reputation_pb2.Message)
    assert message.WhichOneof("asset") == "ipv4"
    assert message.ipv4.host == "192.0.2.1"


def testSerialize_whenSourceMissing_shouldRaiseEncodeError() -> None:
    with pytest.raises(protobuf_message.EncodeError):
        serializer.serialize(
            "v3.report.reputation",
            {"domain_name": {"name": "example.com"}, "listed": True},
        ).SerializeToString()
