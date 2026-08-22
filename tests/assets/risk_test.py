"""Unit tests for Risk asset."""

from ostorlab.agent.message import serializer
from ostorlab.assets import risk, domain_name, ipv4, ios_testflight, file as file_asset


def testRiskAssetToProto_whenDomainTarget_generatesProto():
    asset = risk.Risk(
        rating="HIGH",
        description="SQL injection detected",
        target=domain_name.DomainName(name="ostorlab.co"),
    )
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.risk", raw)
    assert unraw.rating == "HIGH"
    assert unraw.description == "SQL injection detected"
    assert unraw.domain_name.name == "ostorlab.co"


def testRiskAssetToProto_whenIpTarget_generatesProto():
    asset = risk.Risk(
        rating="MEDIUM",
        description="Port 22 open",
        target=ipv4.IPv4(host="1.1.1.1", mask="32"),
    )
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.risk", raw)
    assert unraw.rating == "MEDIUM"
    assert unraw.description == "Port 22 open"
    assert unraw.ipv4.host == "1.1.1.1"


def testRiskAssetToProto_whenIosTestflightTarget_generatesProto():
    asset = risk.Risk(
        rating="CRITICAL",
        description="Insecure TestFlight build",
        target=ios_testflight.IOSTestflight(
            application_url="https://testflight.apple.com/join/vP31q8"
        ),
    )
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.risk", raw)
    assert unraw.rating == "CRITICAL"
    assert (
        unraw.ios_testflight.application_url
        == "https://testflight.apple.com/join/vP31q8"
    )


def testRiskAssetToProto_whenFileTarget_generatesProto():
    asset = risk.Risk(
        rating="LOW",
        description="Public S3 bucket file",
        target=file_asset.File(content_url="https://s3.amazonaws.com/test.txt"),
    )
    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.risk", raw)
    assert unraw.rating == "LOW"
    assert unraw.file.content_url == "https://s3.amazonaws.com/test.txt"
