"""Unit tests for the http fingerprint protobuf message."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.fingerprint.domain_name.service.http import (
    http_pb2,
)


def testSerialize_whenAllFieldsSet_shouldSerializeAndDeserializeCorrectly() -> None:
    raw = serializer.serialize(
        "v3.fingerprint.domain_name.service.http",
        {
            "name": "www.ostorlab.co",
            "port": 443,
            "schema": "https",
            "url": "https://ostorlab.co/",
            "request_count": 99,
            "transferred_bytes": 1840128,
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

    message = serializer.deserialize("v3.fingerprint.domain_name.service.http", raw)

    assert isinstance(message, http_pb2.Message)
    assert message.name == "www.ostorlab.co"
    assert message.port == 443
    assert message.schema == "https"
    assert message.url == "https://ostorlab.co/"
    assert message.request_count == 99
    assert message.transferred_bytes == 1840128
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
        "v3.fingerprint.domain_name.service.http",
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

    message = serializer.deserialize("v3.fingerprint.domain_name.service.http", raw)

    assert isinstance(message, http_pb2.Message)
    assert message.cookies[0].HasField("expires") is False
    assert message.cookies[0].http_only is True
    assert list(message.contacted_hosts) == []
