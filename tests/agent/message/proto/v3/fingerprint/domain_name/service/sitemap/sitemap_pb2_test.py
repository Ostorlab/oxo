"""Unit tests for the sitemap fingerprint protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.domain_name.service.sitemap import (
    sitemap_pb2,
)


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.service.sitemap",
        {
            "name": "ostorlab.co",
            "port": 443,
            "schema": "https",
            "sitemaps": [
                "https://ostorlab.co/sitemap.xml",
                "https://ostorlab.co/__sitemap__/en-US.xml",
            ],
            "page_count": 520,
            "truncated": False,
            "last_modified": "2026-11-08T14:02:11+00:00",
            "languages": ["en-US", "fr-FR"],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.service.sitemap", raw)

    assert isinstance(message, sitemap_pb2.Message)
    assert message.name == "ostorlab.co"
    assert message.port == 443
    assert message.schema == "https"
    assert list(message.sitemaps) == [
        "https://ostorlab.co/sitemap.xml",
        "https://ostorlab.co/__sitemap__/en-US.xml",
    ]
    assert message.page_count == 520
    assert message.HasField("truncated") is True
    assert message.truncated is False
    assert message.last_modified == "2026-11-08T14:02:11+00:00"
    assert list(message.languages) == ["en-US", "fr-FR"]


def testSerialize_whenReadingStoppedAtTheLimit_shouldKeepTheTruncatedCount() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.service.sitemap",
        {
            "name": "stripe.com",
            "port": 443,
            "schema": "https",
            "sitemaps": ["https://stripe.com/sitemap/sitemap.xml"],
            "page_count": 2000,
            "truncated": True,
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.service.sitemap", raw)

    assert isinstance(message, sitemap_pb2.Message)
    assert message.page_count == 2000
    assert message.truncated is True
    assert message.HasField("last_modified") is False
    assert list(message.languages) == []
