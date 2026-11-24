"""Unit tests for the subdomains fingerprint protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.domain_name.subdomains import (
    subdomains_pb2,
)


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.subdomains",
        {
            "name": "monzo.com",
            "subdomains": ["api.monzo.com", "status.monzo.com", "www.monzo.com"],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.subdomains", raw)

    assert isinstance(message, subdomains_pb2.Message)
    assert message.name == "monzo.com"
    assert list(message.subdomains) == [
        "api.monzo.com",
        "status.monzo.com",
        "www.monzo.com",
    ]


def testSerialize_whenNoSubdomainIsFound_shouldKeepTheName() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.subdomains",
        {"name": "example.com", "subdomains": []},
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.subdomains", raw)

    assert isinstance(message, subdomains_pb2.Message)
    assert message.name == "example.com"
    assert len(message.subdomains) == 0
