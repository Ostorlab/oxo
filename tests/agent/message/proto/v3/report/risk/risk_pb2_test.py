"""Unit tests for risk protobuf message with api_schema field."""

from src.ostorlab.agent.message.proto.v3.asset.file.api_schema import api_schema_pb2
from src.ostorlab.agent.message.proto.v3.asset.file.repository_archive import (
    repository_archive_pb2,
)
from src.ostorlab.agent.message.proto.v3.asset.phone_number import phone_number_pb2
from src.ostorlab.agent.message.proto.v3.asset.repository import repository_pb2
from src.ostorlab.agent.message.proto.v3.asset.store.ios_testflight import (
    ios_testflight_pb2,
)
from src.ostorlab.agent.message.proto.v3.report.risk import risk_pb2


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


def testMessage_whenCreateWithRepository_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
    """Test that risk message with repository asset serializes correctly."""
    repository_asset = repository_pb2.Message()
    repository_asset.repository_url = "https://github.com/org/repo.git"
    repository_asset.commit_hash = "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"

    risk_message = risk_pb2.Message()
    risk_message.repository.CopyFrom(repository_asset)
    risk_message.description = "Repository exposes secrets"
    risk_message.rating = "CRITICAL"

    serialized = risk_message.SerializeToString()
    deserialized = risk_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.repository.repository_url == "https://github.com/org/repo.git"
    assert (
        deserialized.repository.commit_hash
        == "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"
    )
    assert deserialized.description == "Repository exposes secrets"
    assert deserialized.rating == "CRITICAL"


def testMessage_whenCreateWithRepositoryArchive_shouldSerializeAndDeserializeCorrectly() -> (
    None
):
    """Test that risk message with repository_archive asset serializes correctly."""
    repository_archive_asset = repository_archive_pb2.Message()
    repository_archive_asset.path = "/tmp/repo.zip"
    repository_archive_asset.content_url = "https://storage.example.com/repo.zip"
    repository_archive_asset.content = b"PK\x03\x04archive-bytes"

    risk_message = risk_pb2.Message()
    risk_message.repository_archive.CopyFrom(repository_archive_asset)
    risk_message.description = "Repository archive exposes secrets"
    risk_message.rating = "CRITICAL"

    serialized = risk_message.SerializeToString()
    deserialized = risk_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.repository_archive.path == "/tmp/repo.zip"
    assert (
        deserialized.repository_archive.content_url
        == "https://storage.example.com/repo.zip"
    )
    assert deserialized.repository_archive.content == b"PK\x03\x04archive-bytes"
    assert deserialized.description == "Repository archive exposes secrets"
    assert deserialized.rating == "CRITICAL"
