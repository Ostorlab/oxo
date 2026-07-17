"""Tests for the asset group protobuf message serialization and deserialization behavior."""

from ostorlab.scanner.proto.assets import asset_group_pb2


def testSerializeAndDeserialize_whenAllAssetTypesSet_returnsEquivalentMessage() -> None:
    message = asset_group_pb2.Message()
    message.files.add(content=b"file-bytes", path="/tmp/a.bin")
    message.ios_ipa.content = b"ipa-bytes"
    message.repositories.add(repository_url="https://example.com/repo.git")
    message.repository_archives.add(content_url="https://example.com/archive.tar.gz")
    message.urls.add(url="https://example.com")
    message.networks.add()
    message.ips.add(host="8.8.8.8")
    message.ipv4s.add(host="1.1.1.1")
    message.ipv6s.add(host="::1")

    serialized = message.SerializeToString()
    deserialized = asset_group_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.files[0].content == b"file-bytes"
    assert deserialized.files[0].path == "/tmp/a.bin"
    assert deserialized.ios_ipa.content == b"ipa-bytes"
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
    message.repositories.add(repository_url="https://example.com/one.git")
    message.repositories.add(repository_url="https://example.com/two.git")

    serialized = message.SerializeToString()
    deserialized = asset_group_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert len(deserialized.files) == 2
    assert deserialized.files[0].content == b"first"
    assert deserialized.files[1].content == b"second"
    assert len(deserialized.repositories) == 2
    assert deserialized.repositories[0].repository_url == "https://example.com/one.git"
    assert deserialized.repositories[1].repository_url == "https://example.com/two.git"


def testMobileAssetOneof_whenSecondAssetSet_keepsOnlyLastAndClearsOthers() -> None:
    message = asset_group_pb2.Message()
    message.android_package_name.package_name = "com.example.app"
    message.ios_ipa.content = b"ipa-bytes"

    serialized = message.SerializeToString()
    deserialized = asset_group_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert deserialized.WhichOneof("mobile_asset") == "ios_ipa"
    assert deserialized.ios_ipa.content == b"ipa-bytes"
    assert deserialized.HasField("android_package_name") is False


def testSerializeAndDeserialize_whenEmpty_returnsEmptyMessage() -> None:
    message = asset_group_pb2.Message()

    serialized = message.SerializeToString()
    deserialized = asset_group_pb2.Message()
    deserialized.ParseFromString(serialized)

    assert len(deserialized.files) == 0
    assert deserialized.WhichOneof("mobile_asset") is None
    assert len(deserialized.repositories) == 0
    assert len(deserialized.urls) == 0
    assert len(deserialized.ips) == 0
