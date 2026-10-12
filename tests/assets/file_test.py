"""Unit tests for File asset."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.asset.file import file_pb2
from ostorlab.assets import file as file_asset


def testFileAsset_whenSelectorIsSetAndCorrect_generatesProto() -> None:
    raw = file_asset.File(content=b"test").to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.file", raw)
    assert isinstance(unraw, file_pb2.Message)
    assert unraw.content == b"test"
