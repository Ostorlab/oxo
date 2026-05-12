from ostorlab.agent.message.proto.v3.asset.repository import repository_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    message = repository_pb2.Message()
    message.content_url = "https://storage.example.com/repo.zip"
    message.repo_url = "https://github.com/org/repo.git"
    message.commit_hash = "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"

    serialized = message.SerializeToString()
    deserialized = repository_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.content_url == "https://storage.example.com/repo.zip"
    assert deserialized.repo_url == "https://github.com/org/repo.git"
    assert deserialized.commit_hash == "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"


def testMessage_whenCreateWithContentBytes_shouldSerializeAndDeserializeCorrectly():
    message = repository_pb2.Message()
    message.content = b"PK\x03\x04archive_content"
    message.repo_url = "https://gitlab.com/org/repo.git"
    message.commit_hash = "b2b20cdbc6551ba359169a3033f193b7f8c1b95e"

    serialized = message.SerializeToString()
    deserialized = repository_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.content == b"PK\x03\x04archive_content"
    assert deserialized.repo_url == "https://gitlab.com/org/repo.git"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    message = repository_pb2.Message()

    assert message.content == b""
    assert message.content_url == ""
    assert message.repo_url == ""
    assert message.commit_hash == ""


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    message = repository_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = repository_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.content == b""
    assert deserialized.content_url == ""
    assert deserialized.repo_url == ""
    assert deserialized.commit_hash == ""
