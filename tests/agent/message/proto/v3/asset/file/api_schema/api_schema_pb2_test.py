from src.ostorlab.agent.message.proto.v3.asset.file.api_schema import api_schema_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    message = api_schema_pb2.Message()
    message.content = b"openapi: 3.0.0"
    message.path = "/api/schema.yaml"
    message.schema_type = "openapi"

    serialized = message.SerializeToString()
    deserialized = api_schema_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.content == b"openapi: 3.0.0"
    assert deserialized.path == "/api/schema.yaml"
    assert deserialized.schema_type == "openapi"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    message = api_schema_pb2.Message()

    assert message.content == b""
    assert message.path == ""
    assert message.schema_type == ""


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    message = api_schema_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = api_schema_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.content == b""
    assert deserialized.path == ""
    assert deserialized.schema_type == ""
