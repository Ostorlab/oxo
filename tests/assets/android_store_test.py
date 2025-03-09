"""Unit tests for Android Store asset."""

import pytest

from ostorlab.assets import android_store


def testAndroidStoreAssetFromDict_withStringValues_returnsExpectedObject():
    """Test AndroidStore.from_dict() returns the expected object."""
    data = {"package_name": "com.test.app"}
    expected_android_store = android_store.AndroidStore(package_name="com.test.app")

    android_store_asset = android_store.AndroidStore.from_dict(data)

    assert android_store_asset == expected_android_store


def testAndroidStoreAssetFromDict_withBytesValues_returnsExpectedObject():
    """Test AndroidStore.from_dict() returns the expected object with bytes values."""
    data = {"package_name": b"com.test.app"}
    expected_android_store = android_store.AndroidStore(package_name="com.test.app")

    android_store_asset = android_store.AndroidStore.from_dict(data)

    assert android_store_asset == expected_android_store


def testAndroidStoreAssetFromDict_missingPackageName_raisesValueError():
    """Test AndroidStore.from_dict() raises ValueError when package_name is missing."""
    with pytest.raises(ValueError, match="package_name is missing."):
        android_store.AndroidStore.from_dict({})
