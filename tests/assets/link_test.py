"""Unit tests for Link asset."""
from ostorlab.agent.message import serializer
from ostorlab.assets import link


def testAssetToProto_whenIP_generatesProto():
    asset = link.Link(url='https://ostorlab.co', method='GET')
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize('v3.asset.link', raw)
    assert unraw.url == 'https://ostorlab.co'
