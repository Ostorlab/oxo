"""Unit tests for the Repository asset class, covering proto serialization and selector behavior."""

from ostorlab.agent.message import serializer
from ostorlab.assets import repository as repository_asset


def testRepositoryAsset_whenSelectorIsSetWithContentUrl_generatesProto():
    raw = repository_asset.Repository(
        content_url="https://storage.example.com/repo.zip",
        repo_url="https://github.com/org/repo.git",
        commit_hash="a1a10cdbc6551ba359169a3033f193b7f8c1b95d",
    ).to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.repository", raw)
    assert unraw.content_url == "https://storage.example.com/repo.zip"
    assert unraw.repo_url == "https://github.com/org/repo.git"
    assert unraw.commit_hash == "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"


def testRepositoryAsset_whenSelectorIsSetWithContent_generatesProto():
    raw = repository_asset.Repository(
        content=b"PK\x03\x04archive",
        repo_url="https://gitlab.com/org/repo.git",
        commit_hash="b2b20cdbc6551ba359169a3033f193b7f8c1b95e",
    ).to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.repository", raw)
    assert unraw.content == b"PK\x03\x04archive"
