"""Tests for ASN and network asset messages."""

import pytest

from ostorlab.agent.message import message


def testMessageSerializeDeserialize_whenASNAsset_preservesASN():
    """Ensure an ASN asset can be serialized and deserialized."""
    serialized = message.Message.from_data(
        "v3.asset.asn",
        {"asn": "AS64500"},
    )

    deserialized = message.Message.from_raw("v3.asset.asn", serialized.raw)

    assert deserialized.data == {"asn": "AS64500"}


@pytest.mark.parametrize(
    ("cidr", "version"),
    (
        ("203.0.113.0/24", 4),
        ("2001:db8:1234::/48", 6),
    ),
)
def testMessageSerializeDeserialize_whenNetworkAsset_preservesOriginRelationship(
    cidr: str, version: int
):
    """Ensure a network asset retains the ASN that announced it."""
    serialized = message.Message.from_data(
        "v3.asset.network",
        {
            "cidr": cidr,
            "version": version,
            "origin_asn": "AS64500",
        },
    )

    deserialized = message.Message.from_raw("v3.asset.network", serialized.raw)

    assert deserialized.data == {
        "cidr": cidr,
        "version": version,
        "origin_asn": "AS64500",
    }
