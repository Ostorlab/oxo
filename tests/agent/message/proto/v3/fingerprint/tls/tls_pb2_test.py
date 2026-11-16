"""Unit tests for the TLS fingerprint protobuf message of a host."""

import pytest

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.tls import tls_pb2


@pytest.mark.parametrize("host", ["example.com", "203.0.113.7", "2001:db8::7"])
def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly(
    host: str,
) -> None:
    """Ensure a message about a domain name, an IPv4 or an IPv6 survives serialization."""
    raw = serializer.serialize(
        "v3.fingerprint.tls",
        {
            "host": host,
            "port": 443,
            "versions": ["TLSv1.2", "TLSv1.3"],
            "ciphers": [
                {"version": "TLSv1.2", "name": "ECDHE-RSA-AES128-GCM-SHA256"},
                {"version": "TLSv1.3", "name": "TLS_AES_256_GCM_SHA384"},
            ],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.tls", raw)

    assert isinstance(message, tls_pb2.Message)
    assert message.host == host
    assert message.port == 443
    assert list(message.versions) == ["TLSv1.2", "TLSv1.3"]
    assert len(message.ciphers) == 2
    assert message.ciphers[0].version == "TLSv1.2"
    assert message.ciphers[0].name == "ECDHE-RSA-AES128-GCM-SHA256"
    assert message.ciphers[1].version == "TLSv1.3"
    assert message.ciphers[1].name == "TLS_AES_256_GCM_SHA384"


def testSerialize_whenNoVersionIsAccepted_shouldKeepThePortAndAnEmptyList() -> None:
    """Ensure serialization keeps the port and an empty list when no version is accepted."""
    raw = serializer.serialize(
        "v3.fingerprint.tls",
        {"host": "example.com", "port": 8443, "versions": [], "ciphers": []},
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.tls", raw)

    assert isinstance(message, tls_pb2.Message)
    assert message.port == 8443
    assert len(message.versions) == 0
    assert len(message.ciphers) == 0
