"""Unit tests for API Schema asset."""

import pytest

from ostorlab.assets import api_schema


def testApiSchemaAssetFromDict_withStringValues_returnsExpectedObject():
    """Test ApiSchema.from_dict() returns the expected object with string values."""
    data = {
        "endpoint_url": "http://example.com/api",
        "content": b"schema_content",
        "content_url": "http://example.com/schema",
        "schema_type": "openapi",
    }
    expected_api_schema = api_schema.ApiSchema(
        endpoint_url="http://example.com/api",
        content=b"schema_content",
        content_url="http://example.com/schema",
        schema_type="openapi",
    )

    api_schema_asset = api_schema.ApiSchema.from_dict(data)

    assert api_schema_asset == expected_api_schema


def testApiSchemaAssetFromDict_withBytesValues_returnsExpectedObject():
    """Test ApiSchema.from_dict() returns the expected object with bytes values."""
    data = {
        "endpoint_url": b"http://example.com/api",
        "content": b"schema_content",
        "content_url": b"http://example.com/schema",
        "schema_type": b"openapi",
    }
    expected_api_schema = api_schema.ApiSchema(
        endpoint_url="http://example.com/api",
        content=b"schema_content",
        content_url="http://example.com/schema",
        schema_type="openapi",
    )

    api_schema_asset = api_schema.ApiSchema.from_dict(data)

    assert api_schema_asset == expected_api_schema


def testApiSchemaAssetFromDict_missingEndpointUrl_raisesValueError():
    """Test ApiSchema.from_dict() raises ValueError when endpoint_url is missing."""
    with pytest.raises(ValueError, match="endpoint_url is missing."):
        api_schema.ApiSchema.from_dict({})
