"""Tests for message module."""

from ostorlab.agent.message import message


def testMessageSerializeDeserialize_whenSelectorIsValid_generatesProperProto():
    """Test message proper serialization from a dict object to a protobuf based on the selector."""
    serialized = message.Message.from_data(
        "v3.fingerprint.file",
        {
            "path": "/etc/hosts",
        },
    )
    deserialized = message.Message.from_raw("v3.fingerprint.file", serialized.raw)

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data.get("path") == "/etc/hosts"


def testMessageSerializeDeserializeWithEnum_whenSelectorIsValid_generatesProperProto():
    """Test message proper serialization with enum from a dict object to a protobuf based on the selector."""
    serialized = message.Message.from_data(
        "v3.report.vulnerability",
        {
            "title": "some_title",
            "technical_detail": "some_details",
            "risk_rating": "MEDIUM",
        },
    )
    deserialized = message.Message.from_raw("v3.report.vulnerability", serialized.raw)

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data.get("risk_rating") == "MEDIUM"


def testMessageSerializeDeserializeForBytes_whenSelectorIsValid_generatesProperProto():
    """Test message proper serialization from a dict object to a protobuf based on the selector."""
    serialized = message.Message.from_data(
        "v3.asset.file",
        {
            "content": b"test",
        },
    )
    deserialized = message.Message.from_raw("v3.asset.file", serialized.raw)

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data.get("content") == b"test"


def testMessageSerializeDeserialize_Forv3CaptureFilesystem_generatesProperProto():
    """Test message proper serialization from a dict object to a protobuf based on the selector."""
    serialized = message.Message.from_data(
        "v3.capture.filesystem",
        {
            "event": "ACCESS",
            "filename": "/etc/hosts",
            "pid": 1,
            "gid": 1,
            "mode": 600,
            "ppid": 1,
            "proc": "init",
        },
    )
    deserialized = message.Message.from_raw("v3.capture.filesystem", serialized.raw)

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data.get("event") == "ACCESS"
    assert deserialized.data.get("filename") == "/etc/hosts"


def testMessageSerializeDeserialize_Forv3FingerprintDomainNameServiceLibrary_generatesProperProto():
    """Test message proper serialization from a dict object to a protobuf based on the selector."""
    serialized = message.Message.from_data(
        "v3.fingerprint.domain_name.service.library",
        {
            "name": "test_service",
            "port": 8080,
            "schema": "https",
            "library_name": "test_library",
            "library_version": "1.0.0",
            "library_type": "test_type",
            "detail": "test_detail",
            "domain_name": "example.com",
        },
    )
    deserialized = message.Message.from_raw(
        "v3.fingerprint.domain_name.service.library", serialized.raw
    )

    assert isinstance(serialized.raw, bytes)
    assert deserialized.data.get("name") == "test_service"
    assert deserialized.data.get("port") == 8080
    assert deserialized.data.get("schema") == "https"
    assert deserialized.data.get("library_name") == "test_library"
    assert deserialized.data.get("library_version") == "1.0.0"
    assert deserialized.data.get("library_type") == "test_type"
    assert deserialized.data.get("detail") == "test_detail"
    assert deserialized.data.get("domain_name") == "example.com"
