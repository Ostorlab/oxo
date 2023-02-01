"""Unit tests for File asset."""
from ostorlab.agent.message import serializer
from ostorlab.assets import file as file_asset


def testFileAsset_whenSelectorIsSetAndCorrect_generatesProto():
    raw = file_asset.File(content=b"test").to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.file", raw)
    assert unraw.content == b"test"
