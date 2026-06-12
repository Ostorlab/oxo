"""Unit tests for the Repository asset class, covering proto serialization and selector behavior."""

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.asset.repository import repository_pb2
from ostorlab.assets import repository as repository_asset


def testToProto_whenRepositoryUrlSet_returnsSerializedBytes():
    raw = repository_asset.Repository(
        repository_url="https://github.com/org/repo.git",
        commit_hash="a1a10cdbc6551ba359169a3033f193b7f8c1b95d",
        provider="GITHUB",
    ).to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.repository", raw)
    assert unraw.repository_url == "https://github.com/org/repo.git"
    assert unraw.commit_hash == "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"
    assert unraw.provider == repository_pb2.Message.GITHUB


def testToProto_whenRepositoryUrlSetAndDifferentCommit_returnsSerializedBytes():
    raw = repository_asset.Repository(
        repository_url="https://gitlab.com/org/repo.git",
        commit_hash="b2b20cdbc6551ba359169a3033f193b7f8c1b95e",
        provider="AZURE",
    ).to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.repository", raw)
    assert unraw.repository_url == "https://gitlab.com/org/repo.git"
    assert unraw.commit_hash == "b2b20cdbc6551ba359169a3033f193b7f8c1b95e"
    assert unraw.provider == repository_pb2.Message.AZURE


def testToProto_whenProviderIsNotSet_returnsSerializedBytes():
    asset = repository_asset.Repository(
        repository_url="https://github.com/org/repo.git",
        commit_hash="a1a10cdbc6551ba359169a3033f193b7f8c1b95d",
    )

    raw = asset.to_proto()

    assert isinstance(raw, bytes)
    assert "provider" not in asset.__dict__
    unraw = serializer.deserialize("v3.asset.repository", raw)
    assert unraw.repository_url == "https://github.com/org/repo.git"
    assert unraw.commit_hash == "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"
