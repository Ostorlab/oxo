"""Tests for the asset group protobuf message serialization and deserialization behavior."""

from ostorlab.agent.message.proto.v3.asset.asset_group import asset_group_pb2


def testSerializeAndDeserialize_whenAllAssetTypesSet_returnsEquivalentMessage() -> None:
    message = asset_group_pb2.Message()
    message.files.add(content=b"file-bytes", path="/tmp/a.bin")
    message.android_apk.add(content=b"apk-bytes")
    message.android_aab.add(content=b"aab-bytes")
    message.ios_ipa.add(content=b"ipa-bytes")
    message.repositories.add(repository_url="https://example.com/repo.git")
    message.repository_archives.add(content_url="https://example.com/archive.tar.gz")
    message.urls.add(url="https://example.com")
    message.ips.add(host="8.8.8.8")
    message.ipv4s.add(host="1.1.1.1")
    message.ipv6s.add(host="::1")

    serialized = message.SerializeToString()
    deserialized = asset_group_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.files[0].content == b"file-bytes"
    assert deserialized.files[0].path == "/tmp/a.bin"
    assert deserialized.android_apk[0].content == b"apk-bytes"
    assert deserialized.android_aab[0].content == b"aab-bytes"
    assert deserialized.ios_ipa[0].content == b"ipa-bytes"
    assert deserialized.repositories[0].repository_url == "https://example.com/repo.git"
    assert (
        deserialized.repository_archives[0].content_url
        == "https://example.com/archive.tar.gz"
    )
    assert deserialized.urls[0].url == "https://example.com"
    assert deserialized.ips[0].host == "8.8.8.8"
    assert deserialized.ipv4s[0].host == "1.1.1.1"
    assert deserialized.ipv6s[0].host == "::1"


def testSerializeAndDeserialize_whenMultipleOfSameType_preservesAllEntries() -> None:
    message = asset_group_pb2.Message()
    message.files.add(content=b"first")
    message.files.add(content=b"second")
    message.android_apk.add(content=b"apk-one")
    message.android_apk.add(content=b"apk-two")

    serialized = message.SerializeToString()
    deserialized = asset_group_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert len(deserialized.files) == 2
    assert deserialized.files[0].content == b"first"
    assert deserialized.files[1].content == b"second"
    assert len(deserialized.android_apk) == 2
    assert deserialized.android_apk[0].content == b"apk-one"
    assert deserialized.android_apk[1].content == b"apk-two"


def testSerializeAndDeserialize_whenEmpty_returnsEmptyMessage() -> None:
    message = asset_group_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = asset_group_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert len(deserialized.files) == 0
    assert len(deserialized.android_apk) == 0
    assert len(deserialized.repositories) == 0
    assert len(deserialized.urls) == 0
    assert len(deserialized.ips) == 0
