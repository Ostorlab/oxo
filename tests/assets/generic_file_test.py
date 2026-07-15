"""Unit tests for the GenericFile asset class, covering proto serialization and selector behavior."""

from ostorlab.agent.message import serializer
from ostorlab.assets import generic_file as generic_file_asset


def testToProto_whenContentUrlSet_returnsSerializedBytes() -> None:
    raw = generic_file_asset.GenericFile(
        content_url="https://example.com/file.bin",
    ).to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.file.generic_file", raw)
    assert unraw.content_url == "https://example.com/file.bin"


def testToProto_whenContentAndPathSet_returnsSerializedBytes() -> None:
    raw = generic_file_asset.GenericFile(
        content=b"file-bytes",
        path="/tmp/file.bin",
    ).to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.file.generic_file", raw)
    assert unraw.content == b"file-bytes"
    assert unraw.path == "/tmp/file.bin"


def testStr_whenContentUrlSet_returnsReadableRepresentation() -> None:
    asset = generic_file_asset.GenericFile(
        content_url="https://example.com/file.bin",
    )

    assert str(asset) == "Generic file:https://example.com/file.bin"


def testStr_whenPathSet_returnsReadableRepresentation() -> None:
    asset = generic_file_asset.GenericFile(
        content=b"file-bytes",
        path="/tmp/file.bin",
    )

    assert str(asset) == "Generic file:/tmp/file.bin"
