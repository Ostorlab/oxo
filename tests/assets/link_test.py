"""Unit tests for Link asset."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.asset.link import link_pb2
from ostorlab.assets import link


def testAssetToProto_whenIP_generatesProto() -> None:
    asset = link.Link(url="https://ostorlab.co", method="GET")
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.link", raw)
    assert isinstance(unraw, link_pb2.Message)
    assert unraw.url == "https://ostorlab.co"
