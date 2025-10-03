import pytest

from ostorlab.agent.message.proto.v3.fingerprint.file.ios.metadata import metadata_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    msg = metadata_pb2.Message()
    msg.bundle_id = "com.example.test"
    
    permission = msg.permissions.add()
    permission.name = "camera"
    permission.usage_description = "App needs camera access"
    
    permission2 = msg.permissions.add()
    permission2.name = "location"
    permission2.usage_description = "App needs location access"
    
    serialized = msg.SerializeToString()
    deserialized_msg = metadata_pb2.Message()
    deserialized_msg.ParseFromString(serialized)
    
    assert deserialized_msg.bundle_id == "com.example.test"
    assert len(deserialized_msg.permissions) == 2
    assert deserialized_msg.permissions[0].name == "camera"
    assert deserialized_msg.permissions[0].usage_description == "App needs camera access"
    assert deserialized_msg.permissions[1].name == "location"
    assert deserialized_msg.permissions[1].usage_description == "App needs location access"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    msg = metadata_pb2.Message()
    
    assert msg.bundle_id == ""
    assert len(msg.permissions) == 0


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    msg = metadata_pb2.Message()
    
    serialized = msg.SerializeToString()
    deserialized_msg = metadata_pb2.Message()
    deserialized_msg.ParseFromString(serialized)
    
    assert deserialized_msg.bundle_id == ""
    assert len(deserialized_msg.permissions) == 0