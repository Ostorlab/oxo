from ostorlab.agent.message.proto.v3.fingerprint.file.ios.feature import feature_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    msg = feature_pb2.Message()
    msg.path = "test/path"
    msg.bundle_id = "com.example.test"
    msg.name = "test_feature"
    msg.description = "Test feature description"
    msg.detail = "Test feature detail"

    serialized = msg.SerializeToString()
    deserialized_msg = feature_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.path == "test/path"
    assert deserialized_msg.bundle_id == "com.example.test"
    assert deserialized_msg.name == "test_feature"
    assert deserialized_msg.description == "Test feature description"
    assert deserialized_msg.detail == "Test feature detail"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    msg = feature_pb2.Message()

    assert msg.path == ""
    assert msg.bundle_id == ""
    assert msg.name == ""
    assert msg.description == ""
    assert msg.detail == ""


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    msg = feature_pb2.Message()
    msg.bundle_id = ""

    serialized = msg.SerializeToString()
    deserialized_msg = feature_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.path == ""
    assert deserialized_msg.bundle_id == ""
    assert deserialized_msg.name == ""
    assert deserialized_msg.description == ""
    assert deserialized_msg.detail == ""
