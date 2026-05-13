"""Tests for the repository protobuf message definitions and serialization behavior."""

from ostorlab.agent.message.proto.v3.asset.repository import repository_pb2


def testSerializeAndDeserialize_whenCreatedWithValidData_returnsEquivalentMessage():
    message = repository_pb2.Message()
    message.origin_url = "https://github.com/org/repo.git"
    message.commit_hash = "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"

    serialized = message.SerializeToString()
    deserialized = repository_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.origin_url == "https://github.com/org/repo.git"
    assert deserialized.commit_hash == "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"


def testCreate_whenEmpty_hasDefaultValues():
    message = repository_pb2.Message()

    assert message.origin_url == ""
    assert message.commit_hash == ""


def testSerializeAndDeserialize_whenEmpty_returnsEmptyMessage():
    message = repository_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = repository_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.origin_url == ""
    assert deserialized.commit_hash == ""
