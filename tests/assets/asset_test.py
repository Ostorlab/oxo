"""Unit tests for asset."""
import dataclasses

from ostorlab.agent.message import serializer
from ostorlab.assets import asset


def testAssetToProto_whenSelectorIsSetAndCorrect_generatesProto():
    @dataclasses.dataclass
    @asset.selector('v3.asset.file.android.apk')
    class SimpleAndroidApk(asset.Asset):
        def __init__(self, content):
            self.content: bytes = content

    raw = SimpleAndroidApk(b'test').to_proto()

    assert isinstance(raw, bytes)
    unraw = serializer.deserialize('v3.asset.file.android.apk', raw)
    assert unraw.content == b'test'
