"""Unit tests for Android AAB asset."""

from ostorlab.assets import android_aab


def testAndroidAabAssetFromDict_withStringValues_returnsExpectedObject():
    """Test AndroidAab.from_dict() returns the expected object."""
    data = {"content": b"aab_content", "path": "/path/to/aab"}
    expected_aab = android_aab.AndroidAab(content=b"aab_content", path="/path/to/aab")
    aab = android_aab.AndroidAab.from_dict(data)
    assert aab == expected_aab


def testAndroidAabAssetFromDict_withBytesValues_returnsExpectedObject():
    """Test AndroidAab.from_dict() returns the expected object with bytes values."""
    data = {"content": b"aab_content", "path": b"/path/to/aab"}
    expected_aab = android_aab.AndroidAab(content=b"aab_content", path="/path/to/aab")
    aab = android_aab.AndroidAab.from_dict(data)
    assert aab == expected_aab
