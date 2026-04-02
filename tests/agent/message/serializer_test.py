"""Tests for serializer module."""

import pytest

from ostorlab.agent.message import serializer


def testSerializeRequest_withFileFingerprint_returnsCorrectProtobufMessage():
    """Test message proper serialization from a dict object to a protobuf based on the selector."""
    serialized = serializer.serialize(
        "v3.fingerprint.file",
        {
            "path": "/etc/hosts",
        },
    )

    assert serialized.path == "/etc/hosts"


def testSerializeRequest_withIncorrectDict_throwsError():
    """Test message serialization error if passed fields are not present in the message definition."""
    with pytest.raises(serializer.SerializationError):
        serializer.serialize(
            "v3.fingerprint.file", {"path": "/etc/hosts", "random": "error"}
        )


def testSerializeRequest_withMissingSelector_throwsError():
    """Test message serialization error if passed fields are not present in the message definition."""
    with pytest.raises(serializer.SerializationError):
        serializer.serialize(
            "v3.random.foo.bar", {"path": "/etc/hosts", "random": "error"}
        )


def testDeserializeRequest_withFileFingerprint_returnsCorrectObjects():
    """Test message proper deserialization based on the selector."""
    serialized = serializer.serialize(
        "v3.fingerprint.file",
        {
            "path": "/etc/hosts",
        },
    )

    deserialized_object = serializer.deserialize(
        "v3.fingerprint.file", serialized.SerializeToString()
    )

    assert deserialized_object.path == "/etc/hosts"


def testDeserializeRequest_withIncorrectSelector_throwsError():
    """Test message deserialization error with incorrect selector."""
    with pytest.raises(serializer.NoMatchingPackageNameError):
        serialized = serializer.serialize(
            "v3.fingerprint.file",
            {
                "path": "/etc/hosts",
            },
        )

        serializer.deserialize("v3.random.foo.bar", serialized.SerializeToString())


def testSerializeScanEventDone_always_returnsCorrectProtobufMessage():
    """Test message serialization with an empty message event message."""
    serialized = serializer.serialize("v3.report.event.scan.done", {})
    assert serialized is not None
    serialized = serializer.serialize("v3.report.event.post_scan.done", {})
    assert serialized is not None


def testFindProtoClass_withValidSelector_returnsProtoClass():
    """Test find_proto_class returns the Message class for a valid selector."""
    proto_class = serializer.find_proto_class("v3.fingerprint.file")

    assert proto_class is not None
    assert proto_class.__name__ == "Message"


def testFindProtoClass_withInvalidSelector_raisesSerializationError():
    """Test find_proto_class raises SerializationError when the module cannot be imported."""
    with pytest.raises(serializer.SerializationError):
        serializer.find_proto_class("v3.nonexistent.selector")


def testFindProtoClass_whenModuleHasNoMessageClass_raisesSerializationError(mocker):
    """Test find_proto_class raises SerializationError when the module lacks the Message class."""
    mock_module = mocker.MagicMock(spec=[])
    mocker.patch("importlib.import_module", return_value=mock_module)

    with pytest.raises(serializer.SerializationError):
        serializer.find_proto_class("v3.fingerprint.file")
