from src.ostorlab.agent.message.proto.v3.asset.file.api_schema.graphql import graphql_pb2


def testMessage_whenCreateWithValidData_shouldSerializeAndDeserializeCorrectly():
    message = graphql_pb2.Message()
    message.content = b"type Query { hello: String }"
    message.path = "/graphql/schema.graphql"
    message.schema_type = "graphql"
    
    serialized = message.SerializeToString()
    deserialized = graphql_pb2.Message()
    deserialized.ParseFromString(serialized)
    
    assert deserialized.content == b"type Query { hello: String }"
    assert deserialized.path == "/graphql/schema.graphql"
    assert deserialized.schema_type == "graphql"


def testMessage_whenCreateEmpty_shouldHaveDefaultValues():
    message = graphql_pb2.Message()

    assert message.content == b""
    assert message.path == ""
    assert message.schema_type == "graphql"
def testMessage_whenSerializeEmpty_shouldDeserializeToEmpty():
    message = graphql_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = graphql_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.content == b""
    assert deserialized.path == ""
    assert deserialized.schema_type == "graphql"