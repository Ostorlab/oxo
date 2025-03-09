"""Unit tests for IP asset."""

import pytest

from ostorlab.agent.message import serializer
from ostorlab.assets import ip


def testAssetToProto_whenIP_generatesProto():
    asset = ip.IP(host="192.168.1.1")
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.ip", raw)
    assert unraw.host == "192.168.1.1"


def testIpAssetFromDict_withStringValues_returnsExpectedObject():
    """Test IP.from_dict() returns the expected object with string values."""
    data = {"host": "127.0.0.1", "version": "4", "mask": "32"}
    expected_ip = ip.IP(host="127.0.0.1", version=4, mask="32")
    ip_asset = ip.IP.from_dict(data)
    assert ip_asset == expected_ip


def testIpAssetFromDict_withBytesValues_returnsExpectedObject():
    """Test IP.from_dict() returns the expected object with bytes values."""
    data = {"host": b"127.0.0.1", "version": b"4", "mask": b"32"}
    expected_ip = ip.IP(host="127.0.0.1", version=4, mask="32")
    ip_asset = ip.IP.from_dict(data)
    assert ip_asset == expected_ip


def testIpAssetFromDict_missingHost_raisesValueError():
    """Test IP.from_dict() raises ValueError when host is missing."""
    with pytest.raises(ValueError, match="host is missing."):
        ip.IP.from_dict({})
