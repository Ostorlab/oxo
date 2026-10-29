from ostorlab.agent.message.proto.v3.asset.store.ios_testflight import (
    ios_testflight_pb2,
)


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
    message = ios_testflight_pb2.Message()
    message.application_url = "https://testflight.apple.com/join/abc123"

    serialized = message.SerializeToString()
    deserialized = ios_testflight_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.application_url == "https://testflight.apple.com/join/abc123"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues() -> None:
    message = ios_testflight_pb2.Message()

    assert message.application_url == ""


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty() -> None:
    message = ios_testflight_pb2.Message()
    message.application_url = ""

    serialized = message.SerializeToString()
    deserialized = ios_testflight_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.application_url == ""


def testMessage_whenCreateWithAppNameOnly_shouldSerializeWithoutApplicationUrl() -> (
    None
):
    message = ios_testflight_pb2.Message()
    message.app_name = "Guest + Uat"

    serialized = message.SerializeToString()
    deserialized = ios_testflight_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.app_name == "Guest + Uat"
    assert deserialized.HasField("application_url") is False


def testMessage_whenCreateWithApplicationUrlAndAppName_shouldKeepBoth() -> None:
    message = ios_testflight_pb2.Message(
        application_url="https://testflight.apple.com/join/abc123",
        app_name="Guest + Uat",
    )

    deserialized = ios_testflight_pb2.Message()
    deserialized.ParseFromString(message.SerializeToString())

    assert deserialized.application_url == "https://testflight.apple.com/join/abc123"
    assert deserialized.app_name == "Guest + Uat"
