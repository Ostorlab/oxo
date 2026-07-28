"""Unit tests for the ASN asset."""

from ostorlab.agent.message import message, serializer
from ostorlab.assets import asn


def testAssetToProto_whenAsnSet_generatesProto() -> None:
    asset = asn.ASN(asn="AS268302")

    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.asn", raw)
    assert unraw.asn == "AS268302"


def testMessageFromData_whenAsn_roundTrips() -> None:
    original = message.Message.from_data("v3.asset.asn", {"asn": "AS268302"})

    restored = message.Message.from_raw("v3.asset.asn", original.raw)

    assert restored.data == {"asn": "AS268302"}
    assert restored.selector == "v3.asset.asn"


def testAsn_whenStr_returnsAsnValue() -> None:
    assert str(asn.ASN(asn="AS268302")) == "AS268302"
