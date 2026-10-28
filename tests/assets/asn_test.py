"""Unit tests for the ASN asset."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.asset.asn import asn_pb2
from ostorlab.assets import asn


def testASNToProto_whenValidData_generatesProto() -> None:
    asset = asn.ASN(asn="15169")

    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.asn", raw)
    assert isinstance(unraw, asn_pb2.Message)
    assert unraw.asn == "15169"
    assert str(asset) == "15169"
    assert asset.proto_field == "asn"
