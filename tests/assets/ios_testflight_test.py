"""Unit tests for the iOS TestFlight asset."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.asset.store.ios_testflight import (
    ios_testflight_pb2,
)
from ostorlab.assets import ios_testflight


def testIOSTestflightToProto_whenApplicationUrl_generatesProtoWithoutAppName() -> None:
    asset = ios_testflight.IOSTestflight(
        application_url="https://testflight.apple.com/join/abc123"
    )

    raw = asset.to_proto()

    unraw = serializer.deserialize("v3.asset.store.ios_testflight", raw)
    assert isinstance(unraw, ios_testflight_pb2.Message)
    assert unraw.application_url == "https://testflight.apple.com/join/abc123"
    assert unraw.HasField("app_name") is False


def testIOSTestflightToProto_whenAppNameOnly_generatesProtoWithoutApplicationUrl() -> (
    None
):
    asset = ios_testflight.IOSTestflight(app_name="Guest + Uat")

    raw = asset.to_proto()

    unraw = serializer.deserialize("v3.asset.store.ios_testflight", raw)
    assert isinstance(unraw, ios_testflight_pb2.Message)
    assert unraw.app_name == "Guest + Uat"
    assert unraw.HasField("application_url") is False


def testIOSTestflightStr_whenAppNameOnly_returnsAppName() -> None:
    asset = ios_testflight.IOSTestflight(app_name="Guest + Uat")

    assert str(asset) == "iOS Testflight (Guest + Uat)"


def testIOSTestflightStr_whenApplicationUrl_returnsApplicationUrl() -> None:
    asset = ios_testflight.IOSTestflight(
        application_url="https://testflight.apple.com/join/abc123",
        app_name="Guest + Uat",
    )

    assert str(asset) == "iOS Testflight (https://testflight.apple.com/join/abc123)"
