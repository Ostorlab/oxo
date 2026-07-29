"""Unit tests for the CIDR network asset."""

import ipaddress

import pytest

from ostorlab.agent.message import message, serializer
from ostorlab.assets import network


def testAssetToProto_whenIpv4Cidr_generatesProto() -> None:
    asset = network.Network(cidr="45.237.228.0/22")

    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.network", raw)
    assert unraw.cidr == "45.237.228.0/22"


def testAssetToProto_whenIpv6Cidr_generatesProto() -> None:
    asset = network.Network(cidr="2001:db8::/32")

    raw = asset.to_proto()

    unraw = serializer.deserialize("v3.asset.network", raw)
    assert unraw.cidr == "2001:db8::/32"


def testMessageFromData_whenIpv4Cidr_roundTrips() -> None:
    original = message.Message.from_data(
        "v3.asset.network", {"cidr": "45.237.228.0/22"}
    )

    restored = message.Message.from_raw("v3.asset.network", original.raw)

    assert restored.data == {"cidr": "45.237.228.0/22"}
    assert restored.selector == "v3.asset.network"


def testMessageFromData_whenIpv6Cidr_roundTrips() -> None:
    original = message.Message.from_data("v3.asset.network", {"cidr": "2001:db8::/32"})

    restored = message.Message.from_raw("v3.asset.network", original.raw)

    assert restored.data == {"cidr": "2001:db8::/32"}


def testNetwork_whenInvalidCidr_raisesValueError() -> None:
    with pytest.raises(ValueError):
        network.Network(cidr="not-a-cidr")


def testNetwork_whenStr_returnsCidrValue() -> None:
    asset = network.Network(cidr="45.237.228.0/22")

    assert str(asset) == "45.237.228.0/22"


def testNetwork_whenNonCanonicalCidr_normalizesToNetworkAddress() -> None:
    asset = network.Network(cidr="192.168.1.100/24")

    assert asset.cidr == "192.168.1.0/24"


def testNetwork_whenCreated_doesNotExposeIpEnumerationFields() -> None:
    asset = network.Network(cidr="45.237.228.0/22")

    assert asset.proto_field == "network"
    assert not hasattr(asset, "host")
    assert not hasattr(asset, "mask")
    assert not hasattr(asset, "version")
    assert isinstance(
        ipaddress.ip_network(asset.cidr, strict=False), ipaddress.IPv4Network
    )
