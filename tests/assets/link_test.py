"""Unit tests for Link asset."""

import pytest

from ostorlab.agent.message import serializer
from ostorlab.assets import link


def testAssetToProto_whenIP_generatesProto():
    asset = link.Link(url="https://ostorlab.co", method="GET")
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.link", raw)
    assert unraw.url == "https://ostorlab.co"


def testLinkAssetFromDict_withStringValues_returnsExpectedObject():
    """Test Link.from_dict() returns the expected object with string values."""
    data = {"url": "http://example.com", "method": "GET"}
    expected_link = link.Link(url="http://example.com", method="GET")
    link_asset = link.Link.from_dict(data)
    assert link_asset == expected_link


def testLinkAssetFromDict_withBytesValues_returnsExpectedObject():
    """Test Link.from_dict() returns the expected object with bytes values."""
    data = {"url": b"http://example.com", "method": b"GET"}
    expected_link = link.Link(url="http://example.com", method="GET")
    link_asset = link.Link.from_dict(data)
    assert link_asset == expected_link


def testLinkAssetFromDict_missingUrl_raisesValueError():
    """Test Link.from_dict() raises ValueError when url is missing."""
    with pytest.raises(ValueError, match="url is missing."):
        link.Link.from_dict({"method": "GET"})


def testLinkAssetFromDict_missingMethod_raisesValueError():
    """Test Link.from_dict() raises ValueError when method is missing."""
    with pytest.raises(ValueError, match="method is missing."):
        link.Link.from_dict({"url": "http://example.com"})
