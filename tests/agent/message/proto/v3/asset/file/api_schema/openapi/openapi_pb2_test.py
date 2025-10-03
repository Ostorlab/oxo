from ostorlab.agent.message.proto.v3.asset.file.api_schema.openapi import openapi_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    message = openapi_pb2.Message()
    message.content = b"openapi: 3.0.0\ninfo:\n  title: API\n  version: 1.0.0"
    message.path = "/openapi/spec.yaml"
    message.schema_type = "openapi"
    
    serialized = message.SerializeToString()
    deserialized = openapi_pb2.Message()
    deserialized.ParseFromString(serialized)
    
    assert deserialized.content == b"openapi: 3.0.0\ninfo:\n  title: API\n  version: 1.0.0"
    assert deserialized.path == "/openapi/spec.yaml"
    assert deserialized.schema_type == "openapi"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    message = openapi_pb2.Message()
    
    assert message.content == b""
    assert message.path == ""
    assert message.schema_type == "openapi"


def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    message = openapi_pb2.Message()
    
    serialized = message.SerializeToString()
    deserialized = openapi_pb2.Message()
    deserialized.ParseFromString(serialized)
    
    assert deserialized.content == b""
    assert deserialized.path == ""
    assert deserialized.schema_type == "openapi"