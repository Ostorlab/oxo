"""Canonical risk references and finding provenance survive the message bus."""

from typing import Any

import pytest
from google.protobuf import descriptor_pb2

from ostorlab.agent.message import message
from ostorlab.agent.message.proto.v3.report.risk import risk_pb2
from ostorlab.assets import risk as risk_asset


def testRiskMessage_whenCanonicalIdProvided_roundTripsReference() -> None:
    payload = {
        "description": "Combine credential exposure and remote access",
        "rating": "HIGH",
        "risk_id": 203,
    }
    outgoing = message.Message.from_data("v3.report.risk", payload)

    incoming = message.Message.from_raw(outgoing.selector, outgoing.raw)

    assert incoming.data == payload


def testRiskMessage_whenSchemaInspected_reservesRemovedLineageFields() -> None:
    schema = descriptor_pb2.FileDescriptorProto.FromString(
        risk_pb2.DESCRIPTOR.serialized_pb
    )
    risk = schema.message_type[0]
    assert {field.name: field.number for field in risk.field}["risk_id"] == 25
    assert "kind" not in {field.name for field in risk.field}
    assert "parent_risk_ids" not in {field.name for field in risk.field}
    assert {"kind", "parent_risk_ids"}.issubset(risk.reserved_name)
    assert all(
        any(reserved.start <= number < reserved.end for reserved in risk.reserved_range)
        for number in (26, 27)
    )


def testRiskMessage_whenLegacyTagsReceived_ignoresRemovedMetadata() -> None:
    raw = bytes.fromhex(
        "5a0f50657273697374656420636861696e620448494748c801cb01"
        "d20105636861696ed80165d80166"
    )

    incoming = message.Message.from_raw("v3.report.risk", raw)

    assert incoming.data == {
        "description": "Persisted chain",
        "rating": "HIGH",
        "risk_id": 203,
    }


def testRiskMessage_whenLegacyPayload_decodesWithoutInventingIdentity() -> None:
    payload = {"description": "Check authentication", "rating": "HIGH"}
    outgoing = message.Message.from_data("v3.report.risk", payload)

    incoming = message.Message.from_raw(outgoing.selector, outgoing.raw)

    assert incoming.data == payload


def testVulnerabilityMessage_whenSourceRisksProvided_roundTripsProvenance() -> None:
    payload = {"title": "Exposed credentials", "source_risk_ids": [101, 102]}
    outgoing = message.Message.from_data("v3.report.vulnerability", payload)

    incoming = message.Message.from_raw(outgoing.selector, outgoing.raw)

    assert incoming.data == payload


def testVulnerabilityMessage_whenLegacyPayload_keepsUnknownOriginAbsent() -> None:
    payload = {"title": "Exposed credentials"}
    outgoing = message.Message.from_data("v3.report.vulnerability", payload)

    incoming = message.Message.from_raw(outgoing.selector, outgoing.raw)

    assert incoming.data == payload


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
    metadata: dict[str, Any] = {
        removed_name: "chain" if removed_name == "kind" else [101, 102]
    }

    with pytest.raises(TypeError, match="unexpected keyword argument"):
        risk_asset.Risk(description="Persisted chain", rating="HIGH", **metadata)
