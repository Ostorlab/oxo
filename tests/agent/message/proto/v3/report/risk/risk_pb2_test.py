"""Unit tests for risk protobuf message with api_schema field."""

from src.ostorlab.agent.message.proto.v3.report.risk import risk_pb2
from src.ostorlab.agent.message.proto.v3.asset.file.api_schema import api_schema_pb2


def testMessage_whenCreateWithApiSchema_shouldSerializeAndDeserializeCorrectly():
    """Test that risk message with api_schema asset serializes correctly."""
    api_schema_asset = api_schema_pb2.Message()
    api_schema_asset.endpoint_url = "https://api.example.com/graphql"
    api_schema_asset.schema_type = "GRAPHQL"

    risk_message = risk_pb2.Message()
    risk_message.api_schema.CopyFrom(api_schema_asset)
    risk_message.description = "GraphQL introspection enabled"
    risk_message.rating = "HIGH"

    serialized = risk_message.SerializeToString()
    deserialized = risk_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.api_schema.endpoint_url == "https://api.example.com/graphql"
    assert deserialized.api_schema.schema_type == "GRAPHQL"
    assert deserialized.description == "GraphQL introspection enabled"
    assert deserialized.rating == "HIGH"
