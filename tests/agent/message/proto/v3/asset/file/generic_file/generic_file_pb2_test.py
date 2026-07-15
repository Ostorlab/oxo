"""Tests for the generic file protobuf message definitions and serialization behavior."""

from ostorlab.agent.message.proto.v3.asset.file.generic_file import (
    generic_file_pb2,
)


def testSerializeAndDeserialize_whenContentUrlSet_returnsEquivalentMessage() -> None:
    message = generic_file_pb2.Message()
    message.content_url = "https://example.com/file.bin"

    serialized = message.SerializeToString()
    deserialized = generic_file_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.content_url == "https://example.com/file.bin"


def testSerializeAndDeserialize_whenContentAndPathSet_returnsEquivalentMessage() -> (
    None
):
    message = generic_file_pb2.Message()
    message.content = b"file-bytes"
    message.path = "/tmp/file.bin"

    serialized = message.SerializeToString()
    deserialized = generic_file_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.content == b"file-bytes"
    assert deserialized.path == "/tmp/file.bin"


def testSerializeAndDeserialize_whenEmpty_returnsEmptyMessage() -> None:
    message = generic_file_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = generic_file_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.HasField("content") is False
    assert deserialized.HasField("path") is False
    assert deserialized.HasField("content_url") is False
