"""Unit tests for Android APK asset."""

from ostorlab.assets import android_apk


def testAndroidApkAssetFromDict_withStringValues_returnsExpectedObject():
    """Test AndroidApk.from_dict() returns the expected object with string values."""
    data = {"content": b"apk_content", "path": "/path/to/apk"}
    expected_apk = android_apk.AndroidApk(content=b"apk_content", path="/path/to/apk")
    apk = android_apk.AndroidApk.from_dict(data)
    assert apk == expected_apk


def testAndroidApkAssetFromDict_withBytesValues_returnsExpectedObject():
    """Test AndroidApk.from_dict() returns the expected object with bytes values."""
    data = {"content": b"apk_content", "path": b"/path/to/apk"}
    expected_apk = android_apk.AndroidApk(content=b"apk_content", path="/path/to/apk")
    apk = android_apk.AndroidApk.from_dict(data)
    assert apk == expected_apk
