"""Unit tests for iOS IPA asset."""

from ostorlab.assets import ios_ipa


def testIosIpaAssetFromDict_withStringValues_returnsExpectedObject():
    """Test IOSIpa.from_dict() returns the expected object."""
    data = {"content": b"ipa_content", "path": "/path/to/ipa"}
    expected_ios_ipa = ios_ipa.IOSIpa(content=b"ipa_content", path="/path/to/ipa")
    ios_ipa_asset = ios_ipa.IOSIpa.from_dict(data)
    assert ios_ipa_asset == expected_ios_ipa


def testIosIpaAssetFromDict_withBytesValues_returnsExpectedObject():
    """Test IOSIpa.from_dict() returns the expected object with bytes values."""
    data = {"content": b"ipa_content", "path": b"/path/to/ipa"}
    expected_ios_ipa = ios_ipa.IOSIpa(content=b"ipa_content", path="/path/to/ipa")
    ios_ipa_asset = ios_ipa.IOSIpa.from_dict(data)
    assert ios_ipa_asset == expected_ios_ipa
