"""Unit tests for IP asset."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.asset.ip.v4 import v4_pb2
from ostorlab.assets import ipv4


def testAssetToProto_whenIPv4_generatesProto() -> None:
    asset = ipv4.IPv4(host="192.168.1.1")
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.ip.v4", raw)
    assert isinstance(unraw, v4_pb2.Message)
    assert unraw.host == "192.168.1.1"
