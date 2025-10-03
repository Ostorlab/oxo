from ostorlab.agent.message.proto.v3.asset.store.ios_testflight import ios_testflight_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    message = ios_testflight_pb2.Message()
    message.application_url = "https://testflight.apple.com/join/abc123"

    serialized = message.SerializeToString()
    deserialized = ios_testflight_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.application_url == "https://testflight.apple.com/join/abc123"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    message = ios_testflight_pb2.Message()

    assert message.application_url == ""


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    message = ios_testflight_pb2.Message()
    message.application_url = ""

    serialized = message.SerializeToString()
    deserialized = ios_testflight_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.application_url == ""