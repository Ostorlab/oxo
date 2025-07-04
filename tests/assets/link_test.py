"""Unit tests for Link asset."""

from ostorlab.agent.message import serializer
from ostorlab.assets import link


def testAssetToProto_whenLinkAsset_generatesProto() -> None:
    """Test that to_proto generates a valid protobuf message for a simple link."""
    asset = link.Link(url="https://ostorlab.co", method="GET")
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.link", raw)
    assert unraw.url == "https://ostorlab.co"
    assert unraw.method == "GET"
    assert not unraw.HasField("body")
    assert len(unraw.extra_headers) == 0
    assert len(unraw.cookies) == 0


def testAssetToProto_whenLinkAssetWithAllFields_generatesProtoCorrectly() -> None:
    """Test that to_proto generates a valid protobuf message with all fields."""
    asset = link.Link(
        url="https://example.com",
        method="POST",
        body=b'{"key": "value"}',
        extra_headers=[
            {"name": "Content-Type", "value": "application/json"},
            {"name": "X-Test", "value": "Test"},
        ],
        cookies=[{"name": "session", "value": "12345"}],
    )

    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.link", raw)
    assert unraw.url == "https://example.com"
    assert unraw.method == "POST"
    assert unraw.body == b'{"key": "value"}'
    assert len(unraw.extra_headers) == 2
    assert unraw.extra_headers[0].name == "Content-Type"
    assert unraw.extra_headers[0].value == "application/json"
    assert unraw.extra_headers[1].name == "X-Test"
    assert unraw.extra_headers[1].value == "Test"
    assert len(unraw.cookies) == 1
    assert unraw.cookies[0].name == "session"
    assert unraw.cookies[0].value == "12345"
