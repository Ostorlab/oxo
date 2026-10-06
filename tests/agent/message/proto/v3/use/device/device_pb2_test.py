"""Tests for the use.device protobuf message definitions and serialization behavior."""

from ostorlab.agent.message.proto.v3.use.device import device_pb2


def testSerializeAndDeserialize_whenCreatedWithValidData_returnsEquivalentMessage():
    message = device_pb2.Message()
    message.device_id = "939AX05RHG"
    message.device_type = "android"
    message.device_name = "sam"
    message.device_version = "11"
    message.device_credentials.login_password.username = "login"
    message.device_credentials.login_password.password = "password"
    message.device_relay.name = "host1"
    message.device_relay.address = "172.19.22.80"
    message.device_relay.port = 22
    message.device_relay_credentials.login_password.username = "relay_login"
    message.device_relay_credentials.login_password.password = "relay_password"
    message.duration.nanos = 100
    message.duration.seconds = 2
    argument = message.args.add()
    argument.arg_name = "package_name"
    argument.arg_value.append("com.test.android")
    message.device_session_token = "5f8c7a2e-1b3d-4e6f-9a0b-1c2d3e4f5a6b"

    serialized = message.SerializeToString()
    deserialized = device_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.device_id == "939AX05RHG"
    assert deserialized.device_type == "android"
    assert deserialized.device_name == "sam"
    assert deserialized.device_version == "11"
    assert deserialized.device_credentials.login_password.username == "login"
    assert deserialized.device_relay.address == "172.19.22.80"
    assert deserialized.device_relay.port == 22
    assert (
        deserialized.device_relay_credentials.login_password.username == "relay_login"
    )
    assert deserialized.duration.seconds == 2
    assert len(deserialized.args) == 1
    assert deserialized.args[0].arg_name == "package_name"
    assert deserialized.device_session_token == "5f8c7a2e-1b3d-4e6f-9a0b-1c2d3e4f5a6b"


def testCreate_whenDeviceSessionTokenNotSet_doesNotHaveDeviceSessionTokenField():
    message = device_pb2.Message()
    message.device_id = "939AX05RHG"

    assert message.HasField("device_session_token") is False


def testSerializeAndDeserialize_whenEmpty_returnsEmptyMessage():
    message = device_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = device_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.device_id == ""
    assert deserialized.HasField("device_session_token") is False
    assert len(deserialized.args) == 0
