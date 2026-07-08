"""Unit tests for the RepositoryArchive asset class, covering proto serialization and selector behavior."""

from ostorlab.agent.message import serializer
from ostorlab.assets import repository_archive as repository_archive_asset


def testToProto_whenContentUrlSet_returnsSerializedBytes() -> None:
    raw = repository_archive_asset.RepositoryArchive(
        content_url="https://example.com/source-archive.tar.gz",
    ).to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.repository_archive", raw)
    assert unraw.content_url == "https://example.com/source-archive.tar.gz"


def testToProto_whenContentAndPathSet_returnsSerializedBytes() -> None:
    raw = repository_archive_asset.RepositoryArchive(
        content=b"archive-bytes",
        path="/tmp/source-archive.tar.gz",
    ).to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.repository_archive", raw)
    assert unraw.content == b"archive-bytes"
    assert unraw.path == "/tmp/source-archive.tar.gz"


def testStr_whenContentUrlSet_returnsReadableRepresentation() -> None:
    asset = repository_archive_asset.RepositoryArchive(
        content_url="https://example.com/source-archive.tar.gz",
    )

    assert str(asset) == "Repository archive:https://example.com/source-archive.tar.gz"


def testStr_whenPathSet_returnsReadableRepresentation() -> None:
    asset = repository_archive_asset.RepositoryArchive(
        content=b"archive-bytes",
        path="/tmp/source-archive.tar.gz",
    )

    assert str(asset) == "Repository archive:/tmp/source-archive.tar.gz"
