"""Unit tests for Domain Name asset."""

import pytest

from ostorlab.assets import domain_name


def test_domain_name_asset_from_dict_returns_expected_object():
    """Test DomainName.from_dict() returns the expected object."""
    data = {"name": "ostorlab.co"}
    expected_domain_name = domain_name.DomainName(name="ostorlab.co")
    domain_name_asset = domain_name.DomainName.from_dict(data)
    assert domain_name_asset == expected_domain_name


def test_domain_name_asset_from_dict_missing_name_raises_value_error():
    """Test DomainName.from_dict() raises ValueError when name is missing."""
    with pytest.raises(ValueError, match="name is missing."):
        domain_name.DomainName.from_dict({})
