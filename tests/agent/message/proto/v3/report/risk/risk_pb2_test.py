"""Unit tests for risk protobuf message with api_schema field."""

from src.ostorlab.agent.message.proto.v3.report.risk import risk_pb2
from src.ostorlab.agent.message.proto.v3.asset.file.api_schema import api_schema_pb2
from src.ostorlab.agent.message.proto.v3.asset.phone_number import phone_number_pb2
from src.ostorlab.agent.message.proto.v3.asset.store.ios_testflight import (
    ios_testflight_pb2,
)


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


def testMessage_whenCreateWithIosTestflight_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
    """Test that risk message with ios_testflight asset serializes correctly."""
    ios_testflight_asset = ios_testflight_pb2.Message()
    ios_testflight_asset.application_url = "https://testflight.apple.com/join/abc123"
    risk_message = risk_pb2.Message()
    risk_message.ios_testflight.CopyFrom(ios_testflight_asset)
    risk_message.description = "Insecure data storage in TestFlight build"
    risk_message.rating = "MEDIUM"

    serialized = risk_message.SerializeToString()
    deserialized = risk_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert (
        deserialized.ios_testflight.application_url
        == "https://testflight.apple.com/join/abc123"
    )
    assert deserialized.description == "Insecure data storage in TestFlight build"
    assert deserialized.rating == "MEDIUM"


def testMessage_whenCreateWithPhoneNumber_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
    """Test that risk message with phone_number asset serializes correctly."""
    phone_number_asset = phone_number_pb2.Message()
    phone_number_asset.number = "+15555550123"

    risk_message = risk_pb2.Message()
    risk_message.phone_number.CopyFrom(phone_number_asset)
    risk_message.description = "Phone-based social engineering risk"
    risk_message.rating = "HIGH"

    serialized = risk_message.SerializeToString()
    deserialized = risk_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.phone_number.number == "+15555550123"
    assert deserialized.description == "Phone-based social engineering risk"
    assert deserialized.rating == "HIGH"
