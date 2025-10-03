from ostorlab.agent.message.proto.v3.fingerprint.file.android.library import library_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    msg = library_pb2.Message()
    msg.path = "test/path"
    msg.package_name = "com.example.test"
    msg.library_name = "test_library"
    msg.library_version = "1.0.0"
    msg.library_type = "native"
    msg.detail = "Test library detail"

    serialized = msg.SerializeToString()
    deserialized_msg = library_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.path == "test/path"
    assert deserialized_msg.package_name == "com.example.test"
    assert deserialized_msg.library_name == "test_library"
    assert deserialized_msg.library_version == "1.0.0"
    assert deserialized_msg.library_type == "native"
    assert deserialized_msg.detail == "Test library detail"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    msg = library_pb2.Message()

    assert msg.path == ""
    assert msg.package_name == ""
    assert msg.library_name == ""
    assert msg.library_version == ""
    assert msg.library_type == ""
    assert msg.detail == ""


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    msg = library_pb2.Message()
    msg.package_name = ""

    serialized = msg.SerializeToString()
    deserialized_msg = library_pb2.Message()
    deserialized_msg.ParseFromString(serialized)

    assert deserialized_msg.path == ""
    assert deserialized_msg.package_name == ""
    assert deserialized_msg.library_name == ""
    assert deserialized_msg.library_version == ""
    assert deserialized_msg.library_type == ""
    assert deserialized_msg.detail == ""
