"""Unit tests for IP asset."""

import pytest

from ostorlab.agent.message import serializer
from ostorlab.assets import ipv4


def testAssetToProto_whenIPv4_generatesProto():
    asset = ipv4.IPv4(host="192.168.1.1")
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.ip.v4", raw)
    assert unraw.host == "192.168.1.1"


def testIpv4AssetFromDict_withStringValues_returnsExpectedObject():
    """Test IPv4.from_dict() returns the expected object with string values."""
    data = {"host": "127.0.0.1", "mask": "32"}
    expected_ipv4 = ipv4.IPv4(host="127.0.0.1", mask="32")
    ipv4_asset = ipv4.IPv4.from_dict(data)
    assert ipv4_asset == expected_ipv4


def testIpv4AssetFromDict_withBytesValues_returnsExpectedObject():
    """Test IPv4.from_dict() returns the expected object with bytes values."""
    data = {"host": b"127.0.0.1", "mask": b"32"}
    expected_ipv4 = ipv4.IPv4(host="127.0.0.1", mask="32")
    ipv4_asset = ipv4.IPv4.from_dict(data)
    assert ipv4_asset == expected_ipv4


def testIpv4AssetFromDict_missingHost_raisesValueError():
    """Test IPv4.from_dict() raises ValueError when host is missing."""
    with pytest.raises(ValueError, match="host is missing."):
        ipv4.IPv4.from_dict({})
