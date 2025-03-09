"""Unit tests for iOS Testflight asset."""

import pytest

from ostorlab.assets import ios_testflight


def testIosTestflightAssetFromDict_withStringValues_returnsExpectedObject():
    """Test IOSTestflight.from_dict() returns the expected object with string values."""
    data = {"application_url": "http://example.com"}
    expected_ios_testflight = ios_testflight.IOSTestflight(
        application_url="http://example.com"
    )

    ios_testflight_asset = ios_testflight.IOSTestflight.from_dict(data)

    assert ios_testflight_asset == expected_ios_testflight


def testIosTestflightAssetFromDict_withBytesValues_returnsExpectedObject():
    """Test IOSTestflight.from_dict() returns the expected object with bytes values."""
    data = {"application_url": b"http://example.com"}
    expected_ios_testflight = ios_testflight.IOSTestflight(
        application_url="http://example.com"
    )

    ios_testflight_asset = ios_testflight.IOSTestflight.from_dict(data)

    assert ios_testflight_asset == expected_ios_testflight


def testIosTestflightAssetFromDict_missingApplicationUrl_raisesValueError():
    """Test IOSTestflight.from_dict() raises ValueError when application_url is missing."""
    with pytest.raises(ValueError, match="package_name is missing."):
        ios_testflight.IOSTestflight.from_dict({})
