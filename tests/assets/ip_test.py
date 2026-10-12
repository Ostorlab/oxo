"""Unit tests for IP asset."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.asset.ip import ip_pb2
from ostorlab.assets import ip


def testAssetToProto_whenIP_generatesProto() -> None:
    asset = ip.IP(host="192.168.1.1")
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.ip", raw)
    assert isinstance(unraw, ip_pb2.Message)
    assert unraw.host == "192.168.1.1"
