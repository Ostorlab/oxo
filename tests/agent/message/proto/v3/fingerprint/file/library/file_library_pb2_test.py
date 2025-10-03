import pytest

from ostorlab.agent.message.proto.v3.fingerprint.file.library import library_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    msg = library_pb2.Message()
    msg.path = "test/path"
    msg.library_name = "test_library"
    msg.library_version = "1.0.0"
    msg.library_type = "shared"
    msg.detail = "Test library detail"
    
    serialized = msg.SerializeToString()
    deserialized_msg = library_pb2.Message()
    deserialized_msg.ParseFromString(serialized)
    
    assert deserialized_msg.path == "test/path"
    assert deserialized_msg.library_name == "test_library"
    assert deserialized_msg.library_version == "1.0.0"
    assert deserialized_msg.library_type == "shared"
    assert deserialized_msg.detail == "Test library detail"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    msg = library_pb2.Message()
    
    assert msg.path == ""
    assert msg.library_name == ""
    assert msg.library_version == ""
    assert msg.library_type == ""
    assert msg.detail == ""


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    msg = library_pb2.Message()
    
    serialized = msg.SerializeToString()
    deserialized_msg = library_pb2.Message()
    deserialized_msg.ParseFromString(serialized)
    
    assert deserialized_msg.path == ""
    assert deserialized_msg.library_name == ""
    assert deserialized_msg.library_version == ""
    assert deserialized_msg.library_type == ""
    assert deserialized_msg.detail == ""