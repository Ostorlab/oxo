"""Unit tests for IP asset."""
from ostorlab.agent.message import serializer
from ostorlab.assets import ip


def testAssetToProto_whenSelectorIsSetAndCorrect_generatesProto():
    asset = ip.IP(host='192.168.1.1')
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize('v3.asset.ip', raw)
    assert unraw.host == '192.168.1.1'
