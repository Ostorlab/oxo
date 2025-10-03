from ostorlab.agent.message.proto.v3.fingerprint.file.android.feature import feature_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    message = feature_pb2.Message()
    message.path = "/system/app/TestApp.apk"
    message.package_name = "com.example.test"
    message.name = "Test Feature"
    message.description = "A test feature for Android"
    message.detail = "Detailed information about the test feature"

    serialized = message.SerializeToString()
    deserialized = feature_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.path == "/system/app/TestApp.apk"
    assert deserialized.package_name == "com.example.test"
    assert deserialized.name == "Test Feature"
    assert deserialized.description == "A test feature for Android"
    assert deserialized.detail == "Detailed information about the test feature"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    message = feature_pb2.Message()

    assert message.path == ""
    assert message.package_name == ""
    assert message.name == ""
    assert message.description == ""
    assert message.detail == ""


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    message = feature_pb2.Message()
    message.package_name = ""

    serialized = message.SerializeToString()
    deserialized = feature_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.path == ""
    assert deserialized.package_name == ""
    assert deserialized.name == ""
    assert deserialized.description == ""
    assert deserialized.detail == ""