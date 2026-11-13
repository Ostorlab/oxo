"""Unit tests for the TLS fingerprint protobuf message of an IPv6 address."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.ip.v6.tls import tls_pb2


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    """Ensure a message with all fields set survives serialization."""
    raw = serializer.serialize(
        "v3.fingerprint.ip.v6.tls",
        {
            "host": "2001:db8::7",
            "mask": "128",
            "version": 6,
            "port": 443,
            "versions": ["TLSv1.2", "TLSv1.3"],
            "ciphers": [
                {"version": "TLSv1.2", "name": "ECDHE-RSA-AES128-GCM-SHA256"},
                {"version": "TLSv1.3", "name": "TLS_AES_256_GCM_SHA384"},
            ],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.ip.v6.tls", raw)

    assert isinstance(message, tls_pb2.Message)
    assert message.host == "2001:db8::7"
    assert message.mask == "128"
    assert message.version == 6
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
        "v3.fingerprint.ip.v6.tls",
        {
            "host": "2001:db8::7",
            "mask": "128",
            "version": 6,
            "port": 8443,
            "versions": [],
            "ciphers": [],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.ip.v6.tls", raw)

    assert isinstance(message, tls_pb2.Message)
    assert message.port == 8443
    assert len(message.versions) == 0
    assert len(message.ciphers) == 0


def testSerialize_whenVersionIsNotSet_shouldDefaultTheVersionTo6() -> None:
    """Ensure serialization defaults the version to 6 when version is not set."""
    raw = serializer.serialize(
        "v3.fingerprint.ip.v6.tls",
        {"host": "2001:db8::7", "port": 443},
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.ip.v6.tls", raw)

    assert isinstance(message, tls_pb2.Message)
    assert message.version == 6
