"""Unit tests for asset."""

import dataclasses

from ostorlab.agent.message import serializer
from ostorlab.agent.message.proto.v3.asset.file.android.apk import apk_pb2
from ostorlab.assets import asset


def testAssetToProto_whenSelectorIsSetAndCorrect_generatesProto() -> None:
    @dataclasses.dataclass
    @asset.selector("v3.asset.file.android.apk")
    class SimpleAndroidApk(asset.Asset):
        content: bytes

    raw = SimpleAndroidApk(b"test").to_proto()
    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.file.android.apk", raw)
    assert isinstance(unraw, apk_pb2.Message)
    assert unraw.content == b"test"
