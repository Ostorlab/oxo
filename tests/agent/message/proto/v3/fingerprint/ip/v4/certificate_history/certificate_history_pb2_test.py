"""Unit tests for the certificate history fingerprint protobuf message of an IPv4 address."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.ip.v4.certificate_history import (
    certificate_history_pb2,
)


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    """Ensure a message with all fields set survives serialization."""
    raw = serializer.serialize(
        "v3.fingerprint.ip.v4.certificate_history",
        {
            "host": "203.0.113.7",
            "mask": "32",
            "version": 4,
            "certificates": [
                {
                    "serial_number": "03a1b2c3d4e5f60718293a4b5c6d7e8f",
                    "issuer": "C=US, O=Let's Encrypt, CN=R11",
                    "common_name": "example.com",
                    "sans": ["example.com", "www.example.com"],
                    "not_before": "2026-09-01T08:00:00Z",
                    "not_after": "2026-11-30T08:00:00Z",
                    "ct_id": 18500000123,
                },
                {
                    "serial_number": "0a0b0c0d",
                    "issuer": "C=US, O=DigiCert Inc, CN=DigiCert TLS RSA SHA256 2020 CA1",
                    "common_name": "example.com",
                    "not_before": "2025-01-10T00:00:00Z",
                    "not_after": "2026-02-10T23:59:59Z",
                    "ct_id": 7,
                },
            ],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.ip.v4.certificate_history", raw)

    assert isinstance(message, certificate_history_pb2.Message)
    assert message.host == "203.0.113.7"
    assert message.mask == "32"
    assert message.version == 4
    assert len(message.certificates) == 2
    current = message.certificates[0]
    assert current.serial_number == "03a1b2c3d4e5f60718293a4b5c6d7e8f"
    assert current.issuer == "C=US, O=Let's Encrypt, CN=R11"
    assert current.common_name == "example.com"
    assert list(current.sans) == ["example.com", "www.example.com"]
    assert current.not_before == "2026-09-01T08:00:00Z"
    assert current.not_after == "2026-11-30T08:00:00Z"
    assert current.ct_id == 18500000123
    previous = message.certificates[1]
    assert previous.serial_number == "0a0b0c0d"
    assert len(previous.sans) == 0
    assert previous.ct_id == 7


def testSerialize_whenCtIdExceeds32Bits_shouldKeepTheFullValue() -> None:
    """Ensure serialization keeps the full value when CT id exceeds 32 bits."""
    ct_id = 2**40 + 5
    raw = serializer.serialize(
        "v3.fingerprint.ip.v4.certificate_history",
        {
            "host": "203.0.113.7",
            "mask": "32",
            "version": 4,
            "certificates": [{"serial_number": "01", "ct_id": ct_id}],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.ip.v4.certificate_history", raw)

    assert isinstance(message, certificate_history_pb2.Message)
    assert message.certificates[0].ct_id == ct_id


def testSerialize_whenNoCertificateIsLogged_shouldKeepAnEmptyList() -> None:
    """Ensure serialization keeps an empty list when no certificate is logged."""
    raw = serializer.serialize(
        "v3.fingerprint.ip.v4.certificate_history",
        {"host": "203.0.113.7", "mask": "32", "version": 4, "certificates": []},
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.ip.v4.certificate_history", raw)

    assert isinstance(message, certificate_history_pb2.Message)
    assert message.host == "203.0.113.7"
    assert message.mask == "32"
    assert message.version == 4
    assert len(message.certificates) == 0


def testSerialize_whenVersionIsNotSet_shouldDefaultTheVersionTo4() -> None:
    """Ensure serialization defaults the version to 4 when version is not set."""
    raw = serializer.serialize(
        "v3.fingerprint.ip.v4.certificate_history",
        {"host": "203.0.113.7", "certificates": []},
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.ip.v4.certificate_history", raw)

    assert isinstance(message, certificate_history_pb2.Message)
    assert message.version == 4
