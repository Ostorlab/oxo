"""Unit tests for the TLS service fingerprint messages of a domain name and of an IP address."""

from typing import Any

import pytest

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.domain_name.service.tls import (
    tls_pb2 as domain_tls_pb2,
)
from ostorlab.agent.message.proto.v3.fingerprint.ip.v4.service.tls import (
    tls_pb2 as ipv4_tls_pb2,
)
from ostorlab.agent.message.proto.v3.fingerprint.ip.v6.service.tls import (
    tls_pb2 as ipv6_tls_pb2,
)

TlsMessage = domain_tls_pb2.Message | ipv4_tls_pb2.Message | ipv6_tls_pb2.Message

_TLS = {
    "port": 443,
    "versions": ["TLSv1.2", "TLSv1.3"],
    "ciphers": [
        {"version": "TLSv1.2", "name": "ECDHE-RSA-AES128-GCM-SHA256"},
        {"version": "TLSv1.3", "name": "TLS_AES_256_GCM_SHA384"},
    ],
}


@pytest.mark.parametrize(
    ("selector", "host"),
    [
        ("v3.fingerprint.domain_name.service.tls", {"name": "example.com"}),
        (
            "v3.fingerprint.ip.v4.service.tls",
            {"host": "203.0.113.7", "mask": "32", "version": 4},
        ),
        (
            "v3.fingerprint.ip.v6.service.tls",
            {"host": "2001:db8::7", "mask": "128", "version": 6},
        ),
    ],
)
def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly(
    selector: str, host: dict[str, Any]
) -> None:
    """Ensure the TLS of a port of a domain name, an IPv4 or an IPv6 survives serialization."""
    raw = serializer.serialize(selector, {**host, **_TLS}).SerializeToString()

    message = serializer.deserialize(selector, raw)

    assert isinstance(message, TlsMessage)
    for key, value in host.items():
        assert getattr(message, key) == value
    assert message.port == 443
    assert list(message.versions) == ["TLSv1.2", "TLSv1.3"]
    assert [(cipher.version, cipher.name) for cipher in message.ciphers] == [
        ("TLSv1.2", "ECDHE-RSA-AES128-GCM-SHA256"),
        ("TLSv1.3", "TLS_AES_256_GCM_SHA384"),
    ]


def testSerialize_whenNoVersionIsAccepted_shouldKeepThePortAndEmptyLists() -> None:
    """Ensure serialization keeps the port and empty lists when no version is accepted."""
    raw = serializer.serialize(
        "v3.fingerprint.ip.v4.service.tls",
        {"host": "203.0.113.7", "port": 8443, "versions": [], "ciphers": []},
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.ip.v4.service.tls", raw)

    assert isinstance(message, ipv4_tls_pb2.Message)
    assert message.port == 8443
    assert message.version == 4
    assert len(message.versions) == 0
    assert len(message.ciphers) == 0
