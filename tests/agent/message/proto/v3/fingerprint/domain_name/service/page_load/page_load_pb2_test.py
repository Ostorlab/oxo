"""Unit tests for the page load fingerprint protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.domain_name.service.page_load import (
    page_load_pb2,
)


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.service.page_load",
        {
            "name": "www.ostorlab.co",
            "port": 443,
            "schema": "https",
            "url": "https://ostorlab.co/",
            "request_count": 99,
            "transferred_bytes": 1840128,
            "dom_content_loaded_ms": 523,
            "load_ms": 740,
            "contacted_hosts": [
                "ostorlab.co",
                "api.ostorlab.co",
                "static.hotjar.com",
                "px.ads.linkedin.com",
            ],
            "cookies": [
                {
                    "name": "_ga",
                    "domain": ".ostorlab.co",
                    "path": "/",
                    "expires": 1797292800,
                    "secure": False,
                    "http_only": False,
                },
                {
                    "name": "bcookie",
                    "domain": ".linkedin.com",
                    "path": "/",
                    "expires": 1825862400,
                    "secure": True,
                    "http_only": False,
                    "same_site": "None",
                },
            ],
        },
    ).SerializeToString()

    message = serializer.deserialize(
        "v3.fingerprint.domain_name.service.page_load", raw
    )

    assert isinstance(message, page_load_pb2.Message)
    assert message.name == "www.ostorlab.co"
    assert message.port == 443
    assert message.schema == "https"
    assert message.url == "https://ostorlab.co/"
    assert message.request_count == 99
    assert message.transferred_bytes == 1840128
    assert message.dom_content_loaded_ms == 523
    assert message.load_ms == 740
    assert list(message.contacted_hosts) == [
        "ostorlab.co",
        "api.ostorlab.co",
        "static.hotjar.com",
        "px.ads.linkedin.com",
    ]
    assert [cookie.name for cookie in message.cookies] == ["_ga", "bcookie"]
    assert message.cookies[0].domain == ".ostorlab.co"
    assert message.cookies[0].expires == 1797292800
    assert message.cookies[0].HasField("same_site") is False
    assert message.cookies[1].secure is True
    assert message.cookies[1].same_site == "None"


def testSerialize_whenCookieLastsTheSession_shouldLeaveItsExpiryOut() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.service.page_load",
        {
            "name": "example.com",
            "port": 443,
            "schema": "https",
            "url": "https://example.com/",
            "request_count": 1,
            "cookies": [
                {
                    "name": "session_id",
                    "domain": "example.com",
                    "path": "/",
                    "secure": True,
                    "http_only": True,
                    "same_site": "Lax",
                }
            ],
        },
    ).SerializeToString()

    message = serializer.deserialize(
        "v3.fingerprint.domain_name.service.page_load", raw
    )

    assert isinstance(message, page_load_pb2.Message)
    assert message.cookies[0].HasField("expires") is False
    assert message.cookies[0].http_only is True
    assert message.HasField("load_ms") is False
    assert list(message.contacted_hosts) == []
