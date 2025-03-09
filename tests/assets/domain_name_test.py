"""Unit tests for Domain Name asset."""

import pytest

from ostorlab.assets import domain_name


def testDomainNameAssetFromDict_withStringValues_returnsExpectedObject():
    """Test DomainName.from_dict() returns the expected object with string values."""
    data = {"name": "ostorlab.co"}
    expected_domain_name = domain_name.DomainName(name="ostorlab.co")

    domain_name_asset = domain_name.DomainName.from_dict(data)

    assert domain_name_asset == expected_domain_name


def testDomainNameAssetFromDict_withBytesValues_returnsExpectedObject():
    """Test DomainName.from_dict() returns the expected object with bytes values."""
    data = {"name": b"ostorlab.co"}
    expected_domain_name = domain_name.DomainName(name="ostorlab.co")

    domain_name_asset = domain_name.DomainName.from_dict(data)

    assert domain_name_asset == expected_domain_name


def testDomainNameAssetFromDict_missingName_raisesValueError():
    """Test DomainName.from_dict() raises ValueError when name is missing."""
    with pytest.raises(ValueError, match="name is missing."):
        domain_name.DomainName.from_dict({})
