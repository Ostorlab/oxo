"""Unit tests for the TLS fingerprint protobuf message of a domain name service."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.domain_name.service.tls import tls_pb2


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    """Ensure a message with all fields set survives serialization."""
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.service.tls",
        {
            "name": "ostorlab.co",
            "port": 443,
            "schema": "https",
            "protocols": [
                {"name": "TLSv1.3", "offered": True},
                {"name": "TLSv1.0", "offered": False},
            ],
            "ciphers": [
                {
                    "protocol": "TLSv1.3",
                    "name": "TLS_AES_256_GCM_SHA384",
                    "key_exchange": "ECDH 253",
                    "encryption": "AESGCM",
                    "bits": 256,
                }
            ],
            "forward_secrecy": True,
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.service.tls", raw)

    assert isinstance(message, tls_pb2.Message)
    assert message.name == "ostorlab.co"
    assert message.port == 443
    assert message.schema == "https"
    assert [(p.name, p.offered) for p in message.protocols] == [
        ("TLSv1.3", True),
        ("TLSv1.0", False),
    ]
    assert len(message.ciphers) == 1
    assert message.ciphers[0].protocol == "TLSv1.3"
    assert message.ciphers[0].name == "TLS_AES_256_GCM_SHA384"
    assert message.ciphers[0].key_exchange == "ECDH 253"
    assert message.ciphers[0].encryption == "AESGCM"
    assert message.ciphers[0].bits == 256
    assert message.forward_secrecy is True


def testSerialize_whenForwardSecrecyIsNotOffered_shouldKeepTheFalseValue() -> None:
    """Ensure a service without forward secrecy is told apart from one that was not checked."""
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.service.tls",
        {"name": "ostorlab.co", "port": 443, "forward_secrecy": False},
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.service.tls", raw)

    assert isinstance(message, tls_pb2.Message)
    assert message.HasField("forward_secrecy") is True
    assert message.forward_secrecy is False
    assert list(message.ciphers) == []
