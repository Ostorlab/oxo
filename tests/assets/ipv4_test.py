"""Unit tests for IP asset."""

from ostorlab.agent.message import serializer
from ostorlab.assets import ipv4


def testAssetToProto_whenIPv4_generatesProto():
    asset = ipv4.IPv4(host="192.168.1.1")
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.ip.v4", raw)
    assert unraw.host == "192.168.1.1"
