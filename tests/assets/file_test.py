"""Unit tests for File asset."""

from ostorlab.agent.message import serializer
from ostorlab.assets import file as file_asset


def testFileAsset_whenSelectorIsSetAndCorrect_generatesProto():
    raw = file_asset.File(
        content=b"test", path="/test", content_url="http://test.com"
    ).to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.file", raw)
    assert unraw.content == b"test"


def test_file_asset_from_dict_success():
    """Test FileAsset.from_dict creates an object when at least one field is provided."""
    data = {"content": b"test_content", "path": "/test/path"}
    file_asset_obj = file_asset.File.from_dict(data)
    assert file_asset_obj.content == b"test_content"
    assert file_asset_obj.path == "/test/path"
