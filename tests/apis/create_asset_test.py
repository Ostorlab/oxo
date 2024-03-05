"""Unittests for the create asset API request."""

import json
import pytest

from ostorlab.assets import ipv4, asset as base_asset, android_aab
from ostorlab.apis import assets


def testcreateAssetApiRequest_whenFilesAreUploaded_returnsRequestWithFilesAndMapVariables():
    """Unittest for create asset API request : Case where the asset has a field of type bytes.
    Request should have a file option, operations & mapping.
    """
    asset = android_aab.AndroidAab(content=b"some_content", path="some/path")
    api_request = assets.CreateAssetAPIRequest(asset)
    request_files = api_request.files
    operations = json.loads(api_request.data["operations"])
    variables = json.loads(operations["variables"])
    map_variables = json.loads(api_request.data["map"])

    assert "operations" in api_request.data
    assert map_variables["0"] == ["variables.asset.androidFile.file"]
    assert variables["asset"]["androidFile"]["file"] is None
    assert request_files["0"] == b"some_content"


def testcreateAssetApiRequest_whenAssetDoesNotRequireUploadedFiles_returnsRequestWithoutFilesAndMapVariables():
    """Unittest for create asset API request : Case where the asset does not require uploaded files"""
    asset = ipv4.IPv4(host="127.0.0.1", version=4, mask="32")
    api_request = assets.CreateAssetAPIRequest(asset)

    assert "operations" not in api_request.data
    assert "map" not in api_request.data


def testcreateAssetApiRequest_whenAssetTypeIsUnknown_raisesNotImplementedError():
    """Unittest for create asset API request : Case where the asset type is not supported."""
    asset = base_asset.Asset()
    api_request = assets.CreateAssetAPIRequest(asset)

    with pytest.raises(NotImplementedError):
        _ = api_request.data
