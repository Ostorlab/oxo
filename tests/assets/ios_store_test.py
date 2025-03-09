"""Unit tests for iOS Store asset."""

import pytest

from ostorlab.assets import ios_store


def testIosStoreAssetFromDict_withStringValues_returnsExpectedObject():
    """Test IOSStore.from_dict() returns the expected object with string values."""
    data = {"bundle_id": "com.test.app"}
    expected_ios_store = ios_store.IOSStore(bundle_id="com.test.app")

    ios_store_asset = ios_store.IOSStore.from_dict(data)

    assert ios_store_asset == expected_ios_store


def testIosStoreAssetFromDict_withBytesValues_returnsExpectedObject():
    """Test IOSStore.from_dict() returns the expected object with bytes values."""
    data = {"bundle_id": b"com.test.app"}
    expected_ios_store = ios_store.IOSStore(bundle_id="com.test.app")

    ios_store_asset = ios_store.IOSStore.from_dict(data)

    assert ios_store_asset == expected_ios_store


def testIosStoreAssetFromDict_missingBundleId_raisesValueError():
    """Test IOSStore.from_dict() raises ValueError when bundle_id is missing."""
    with pytest.raises(ValueError, match="bundle_id is missing."):
        ios_store.IOSStore.from_dict({})
