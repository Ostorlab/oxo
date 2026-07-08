"""Tests for the repository archive protobuf message definitions and serialization behavior."""

from ostorlab.agent.message.proto.v3.asset.repository_archive import (
    repository_archive_pb2,
)


def testSerializeAndDeserialize_whenContentUrlSet_returnsEquivalentMessage() -> None:
    message = repository_archive_pb2.Message()
    message.content_url = "https://example.com/source-archive.tar.gz"

    serialized = message.SerializeToString()
    deserialized = repository_archive_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.content_url == "https://example.com/source-archive.tar.gz"


def testSerializeAndDeserialize_whenContentAndPathSet_returnsEquivalentMessage() -> (
    None
):
    message = repository_archive_pb2.Message()
    message.content = b"archive-bytes"
    message.path = "/tmp/source-archive.tar.gz"

    serialized = message.SerializeToString()
    deserialized = repository_archive_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.content == b"archive-bytes"
    assert deserialized.path == "/tmp/source-archive.tar.gz"


def testSerializeAndDeserialize_whenEmpty_returnsEmptyMessage() -> None:
    message = repository_archive_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = repository_archive_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.HasField("content") is False
    assert deserialized.HasField("path") is False
    assert deserialized.HasField("content_url") is False
