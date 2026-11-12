"""Unit tests for the lookalike domains fingerprint protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.domain_name.lookalikes import (
    lookalikes_pb2,
)


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.lookalikes",
        {
            "name": "paypal.com",
            "checked_count": 412,
            "lookalikes": [
                {
                    "name": "xn--pypal-4ve.com",
                    "unicode_name": "pаypal.com",
                    "kind": "homoglyph",
                    "nameservers": ["ns1.example.net", "ns2.example.net"],
                    "addresses": ["203.0.113.7", "2001:db8::7"],
                    "mail_servers": ["mx.example.net"],
                    "registered_at": "2026-10-02T09:14:00Z",
                    "registrar": "Example Registrar, Inc.",
                    "shares_nameservers": False,
                },
                {
                    "name": "paypal.fr",
                    "kind": "other_tld",
                    "nameservers": ["ns1.p57.dynect.net"],
                    "shares_nameservers": True,
                },
            ],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.lookalikes", raw)

    assert isinstance(message, lookalikes_pb2.Message)
    assert message.name == "paypal.com"
    assert message.checked_count == 412
    assert len(message.lookalikes) == 2
    homoglyph = message.lookalikes[0]
    assert homoglyph.name == "xn--pypal-4ve.com"
    assert homoglyph.unicode_name == "pаypal.com"
    assert homoglyph.kind == "homoglyph"
    assert list(homoglyph.nameservers) == ["ns1.example.net", "ns2.example.net"]
    assert list(homoglyph.addresses) == ["203.0.113.7", "2001:db8::7"]
    assert list(homoglyph.mail_servers) == ["mx.example.net"]
    assert homoglyph.registered_at == "2026-10-02T09:14:00Z"
    assert homoglyph.registrar == "Example Registrar, Inc."
    assert homoglyph.HasField("shares_nameservers") is True
    assert homoglyph.shares_nameservers is False
    assert message.lookalikes[1].shares_nameservers is True


def testSerialize_whenNoLookalikeIsRegistered_shouldKeepTheCheckedCount() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.lookalikes",
        {"name": "example.com", "checked_count": 0, "lookalikes": []},
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.lookalikes", raw)

    assert isinstance(message, lookalikes_pb2.Message)
    assert message.name == "example.com"
    assert message.HasField("checked_count") is True
    assert message.checked_count == 0
    assert len(message.lookalikes) == 0
