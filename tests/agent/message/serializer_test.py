"""Tests for serializer module."""

import dataclasses
import pathlib

import pytest

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.asset.multi_asset import multi_asset_pb2
from ostorlab.agent.message.proto.v3.fingerprint.file import file_pb2
from ostorlab.agent.message.proto.v3.use.device import device_pb2
from ostorlab.assets import android_store as android_store_asset
from ostorlab.assets import link as link_asset


def testSerializeRequest_withProtobufStubSibling_returnsCorrectProtobufMessage(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Typing stub siblings do not create ambiguous message selector matches."""
    message_directory = (
        tmp_path
        / "ostorlab"
        / "agent"
        / "message"
        / "proto"
        / "v3"
        / "fingerprint"
        / "file"
    )
    message_directory.mkdir(parents=True)
    (message_directory / "file_pb2.py").write_text("", encoding="utf-8")
    (message_directory / "file_pb2.pyi").write_text("", encoding="utf-8")
    monkeypatch.setattr(serializer, "MESSAGE_CODE_PATH", tmp_path)

    serialized = serializer.serialize("v3.fingerprint.file", {"path": "/etc/hosts"})

    assert isinstance(serialized, file_pb2.Message)
    assert serialized.path == "/etc/hosts"


def testSerializeRequest_withFileFingerprint_returnsCorrectProtobufMessage() -> None:
    """Test message proper serialization from a dict object to a protobuf based on the selector."""
    serialized = serializer.serialize(
        "v3.fingerprint.file",
        {
            "path": "/etc/hosts",
        },
    )

    assert isinstance(serialized, file_pb2.Message)
    assert serialized.path == "/etc/hosts"


def testSerializeRequest_withIncorrectDict_throwsError() -> None:
    """Test message serialization error if passed fields are not present in the message definition."""
    with pytest.raises(serializer.SerializationError):
        serializer.serialize(
            "v3.fingerprint.file", {"path": "/etc/hosts", "random": "error"}
        )


def testSerializeRequest_withMissingSelector_throwsError() -> None:
    """Test message serialization error if passed fields are not present in the message definition."""
    with pytest.raises(serializer.SerializationError):
        serializer.serialize(
            "v3.random.foo.bar", {"path": "/etc/hosts", "random": "error"}
        )


def testDeserializeRequest_withFileFingerprint_returnsCorrectObjects() -> None:
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

    assert isinstance(deserialized_object, file_pb2.Message)
    assert deserialized_object.path == "/etc/hosts"


def testDeserializeRequest_withIncorrectSelector_throwsError() -> None:
    """Test message deserialization error with incorrect selector."""
    with pytest.raises(serializer.NoMatchingPackageNameError):
        serialized = serializer.serialize(
            "v3.fingerprint.file",
            {
                "path": "/etc/hosts",
            },
        )

        serializer.deserialize("v3.random.foo.bar", serialized.SerializeToString())


def testSerializeScanEventDone_always_returnsCorrectProtobufMessage() -> None:
    """Test message serialization with an empty message event message."""
    serialized = serializer.serialize("v3.report.event.scan.done", {})
    assert serialized is not None
    serialized = serializer.serialize("v3.report.event.post_scan.done", {})
    assert serialized is not None


def testSerialize_whenDataclassValue_shouldRecurseIntoNestedFields() -> None:
    """A dataclass value is recursed into instead of being set directly."""
    serialized = serializer.serialize(
        "v3.asset.multi_asset",
        {"android_store": android_store_asset.AndroidStore(package_name="com.a.b")},
    )

    assert isinstance(serialized, multi_asset_pb2.Message)
    assert serialized.android_store.package_name == "com.a.b"


def testSerialize_whenListOfDataclasses_shouldRecurseIntoEachItem() -> None:
    """Each dataclass in a repeated field is recursed into and appended."""
    serialized = serializer.serialize(
        "v3.asset.multi_asset",
        {
            "urls": [
                link_asset.Link(url="https://example.com/1", method="GET"),
                link_asset.Link(url="https://example.com/2", method="POST"),
            ]
        },
    )

    assert isinstance(serialized, multi_asset_pb2.Message)
    assert [(url.url, url.method) for url in serialized.urls] == [
        ("https://example.com/1", "GET"),
        ("https://example.com/2", "POST"),
    ]


def testSerialize_whenDataclassWithInvalidField_shouldRaiseSerializationError() -> None:
    """A dataclass field absent from the proto raises SerializationError, not AttributeError."""

    @dataclasses.dataclass
    class _InvalidAsset:
        not_a_proto_field: str = "value"

    with pytest.raises(serializer.SerializationError):
        serializer.serialize("v3.asset.multi_asset", {"android_store": _InvalidAsset()})


def testSerializeAndDeserialize_withUseDeviceSessionToken_returnsCorrectObject() -> (
    None
):
    """A use.device message carrying a device_session_token round-trips correctly.

    Regression test for the DaaS device_session_token field: agents allocating a
    device through the scanning engine's Device-as-a-Service API need this field
    to authenticate DaaS device-action calls for that allocation.
    """
    serialized = serializer.serialize(
        "v3.use.device",
        {
            "device_id": "939AX05RHG",
            "device_type": "android",
            "device_version": "11",
            "device_session_token": "5f8c7a2e-1b3d-4e6f-9a0b-1c2d3e4f5a6b",
        },
    )

    deserialized_object = serializer.deserialize(
        "v3.use.device", serialized.SerializeToString()
    )

    assert isinstance(deserialized_object, device_pb2.Message)
    assert deserialized_object.device_id == "939AX05RHG"
    assert (
        deserialized_object.device_session_token
        == "5f8c7a2e-1b3d-4e6f-9a0b-1c2d3e4f5a6b"
    )
