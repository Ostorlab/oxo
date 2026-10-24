"""Risk lineage remains intact across the agent message bus."""

from ostorlab.agent.message import message
from ostorlab.assets import risk as risk_asset


def testRiskMessage_whenMultipleParents_roundTripsLineage() -> None:
    payload = {
        "description": "Combine credential exposure and remote access",
        "rating": "HIGH",
        "risk_id": 203,
        "kind": "chain",
        "parent_risk_ids": [101, 102],
    }
    outgoing = message.Message.from_data("v3.report.risk", payload)

    incoming = message.Message.from_raw(outgoing.selector, outgoing.raw)

    assert incoming.data == payload


def testRiskMessage_whenLegacyPayload_hasNoFabricatedParents() -> None:
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


def testRiskAsset_whenInjectedWithParents_preservesCanonicalIdentity() -> None:
    asset = risk_asset.Risk(
        description="Combine credential exposure and remote access",
        rating="HIGH",
        risk_id=203,
        kind="chain",
        parent_risk_ids=[101, 102],
    )

    incoming = message.Message.from_raw(asset.selector, asset.to_proto())

    assert incoming.data["risk_id"] == 203
    assert incoming.data["kind"] == "chain"
    assert incoming.data["parent_risk_ids"] == [101, 102]
