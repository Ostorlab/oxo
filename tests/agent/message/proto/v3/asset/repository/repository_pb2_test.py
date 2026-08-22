"""Tests for the repository protobuf message definitions and serialization behavior."""

from ostorlab.agent.message.proto.v3.asset.repository import repository_pb2


def testSerializeAndDeserialize_whenCreatedWithValidData_returnsEquivalentMessage():
    message = repository_pb2.Message()
    message.repository_url = "https://github.com/org/repo.git"
    message.commit_hash = "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"
    message.provider = repository_pb2.Message.GITLAB

    serialized = message.SerializeToString()
    deserialized = repository_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.repository_url == "https://github.com/org/repo.git"
    assert deserialized.commit_hash == "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"
    assert deserialized.provider == repository_pb2.Message.GITLAB


def testCreate_whenProviderNotSet_doesNotHaveProviderField():
    message = repository_pb2.Message()

    assert message.repository_url == ""
    assert message.commit_hash == ""
    assert message.HasField("provider") is False


def testSerializeAndDeserialize_whenEmpty_returnsEmptyMessage():
    message = repository_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = repository_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.repository_url == ""
    assert deserialized.commit_hash == ""
    assert deserialized.HasField("provider") is False
