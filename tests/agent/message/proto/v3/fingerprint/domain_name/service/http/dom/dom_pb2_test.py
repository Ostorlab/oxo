"""Unit tests for the http dom fingerprint protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.domain_name.service.http import (
    http_pb2,
)
from ostorlab.agent.message.proto.v3.fingerprint.domain_name.service.http.dom import (
    dom_pb2,
)


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.service.http.dom",
        {
            "name": "www.ostorlab.co",
            "port": 443,
            "schema": "https",
            "url": "https://ostorlab.co/",
            "dom_content_loaded_ms": 523,
            "load_ms": 740,
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.service.http.dom", raw)

    assert isinstance(message, dom_pb2.Message)
    assert message.name == "www.ostorlab.co"
    assert message.port == 443
    assert message.schema == "https"
    assert message.url == "https://ostorlab.co/"
    assert message.dom_content_loaded_ms == 523
    assert message.load_ms == 740


def testSerialize_whenPageStillLoading_shouldLeaveTheLoadTimeOut() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.service.http.dom",
        {
            "name": "example.com",
            "port": 443,
            "schema": "https",
            "url": "https://example.com/",
            "dom_content_loaded_ms": 523,
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.service.http.dom", raw)

    assert isinstance(message, dom_pb2.Message)
    assert message.HasField("load_ms") is False


def testSerialize_whenSelectorIsTheParentHttp_shouldUseTheHttpMessage() -> None:
    """The http and http.dom messages sit one inside the other, each selector keeps its own."""
    http_message = serializer.serialize(
        "v3.fingerprint.domain_name.service.http", {"name": "example.com"}
    )
    dom_message = serializer.serialize(
        "v3.fingerprint.domain_name.service.http.dom", {"name": "example.com"}
    )

    assert isinstance(http_message, http_pb2.Message)
    assert isinstance(dom_message, dom_pb2.Message)


def testSerialize_whenPageHasMetadata_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.service.http.dom",
        {
            "name": "ostorlab.co",
            "port": 443,
            "schema": "https",
            "url": "https://ostorlab.co/",
            "title": "Ostorlab",
            "description": "Mobile and web security scanner.",
            "language": "en",
            "open_graph": [
                {"name": "og:title", "content": "Ostorlab"},
                {"name": "og:type", "content": "website"},
            ],
            "twitter": [{"name": "twitter:card", "content": "summary_large_image"}],
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.service.http.dom", raw)

    assert isinstance(message, dom_pb2.Message)
    assert message.title == "Ostorlab"
    assert message.description == "Mobile and web security scanner."
    assert message.language == "en"
    assert [(tag.name, tag.content) for tag in message.open_graph] == [
        ("og:title", "Ostorlab"),
        ("og:type", "website"),
    ]
    assert [(tag.name, tag.content) for tag in message.twitter] == [
        ("twitter:card", "summary_large_image")
    ]


def testSerialize_whenPageHasNoMetadata_shouldLeaveItOut() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.service.http.dom",
        {
            "name": "example.com",
            "port": 443,
            "schema": "https",
            "url": "https://example.com/",
            "load_ms": 740,
        },
    ).SerializeToString()

    message = serializer.deserialize("v3.fingerprint.domain_name.service.http.dom", raw)

    assert isinstance(message, dom_pb2.Message)
    assert message.HasField("title") is False
    assert message.HasField("description") is False
    assert message.HasField("language") is False
    assert list(message.open_graph) == []
    assert list(message.twitter) == []
