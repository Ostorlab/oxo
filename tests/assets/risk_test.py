"""Risk assets expose canonical references without obsolete wire metadata."""

import typing

import pytest

from ostorlab.agent.message import message
from ostorlab.assets import risk as risk_asset


def testRiskAsset_whenCanonicalIdProvided_preservesReference() -> None:
    asset = risk_asset.Risk(
        description="Combine credential exposure and remote access",
        rating="HIGH",
        risk_id=203,
    )

    incoming = message.Message.from_raw(asset.selector, asset.to_proto())

    assert incoming.data == {
        "description": "Combine credential exposure and remote access",
        "rating": "HIGH",
        "risk_id": 203,
    }


@pytest.mark.parametrize("removed_name", ["kind", "parent_risk_ids"])
def testRiskAsset_whenRemovedMetadataProvided_rejectsConstructorArgument(
    removed_name: str,
) -> None:
    metadata: dict[str, typing.Any] = {
        removed_name: "chain" if removed_name == "kind" else [101, 102]
    }

    with pytest.raises(TypeError, match="unexpected keyword argument"):
        risk_asset.Risk(description="Persisted chain", rating="HIGH", **metadata)
