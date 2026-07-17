"""Unit tests for the MultiAsset target."""

import pytest

from ostorlab.agent.message.proto.v3.asset.multi_asset import multi_asset_pb2
from ostorlab.assets import android_apk as android_apk_asset
from ostorlab.assets import android_store as android_store_asset
from ostorlab.assets import domain_name as domain_name_asset
from ostorlab.assets import ios_store as ios_store_asset
from ostorlab.assets import ipv4 as ipv4_asset
from ostorlab.assets import ipv6 as ipv6_asset
from ostorlab.assets import link as link_asset
from ostorlab.assets import multi_asset as multi_asset_asset


def testMultiAssetToProto_whenMixedTargets_shouldBundleAllAssets() -> None:
    asset = multi_asset_asset.MultiAsset(
        targets=[
            ipv4_asset.IPv4(host="8.8.8.8", mask="24"),
            ipv6_asset.IPv6(host="::1"),
            link_asset.Link(url="https://ostorlab.co", method="GET"),
            android_apk_asset.AndroidApk(content=b"apk-bytes", path="/tmp/app.apk"),
        ]
    )

    raw = asset.to_proto()

    message = multi_asset_pb2.Message()
    message.ParseFromString(raw)
    assert message.ipv4s[0].host == "8.8.8.8"
    assert message.ipv4s[0].mask == "24"
    assert message.ipv4s[0].version == 4
    assert message.ipv6s[0].host == "::1"
    assert message.ipv6s[0].version == 6
    assert message.urls[0].url == "https://ostorlab.co"
    assert message.WhichOneof("mobile_asset") == "android_apk"
    assert message.android_apk.content == b"apk-bytes"
    assert message.android_apk.path == "/tmp/app.apk"


def testMultiAssetToProto_whenStoreAsset_shouldSetMobileOneof() -> None:
    asset = multi_asset_asset.MultiAsset(
        targets=[android_store_asset.AndroidStore(package_name="com.example.app")]
    )

    raw = asset.to_proto()

    message = multi_asset_pb2.Message()
    message.ParseFromString(raw)
    assert message.WhichOneof("mobile_asset") == "android_package_name"
    assert message.android_package_name.package_name == "com.example.app"


def testMultiAssetToProto_whenTwoMobileAssets_shouldRaiseValueError() -> None:
    asset = multi_asset_asset.MultiAsset(
        targets=[
            android_store_asset.AndroidStore(package_name="com.example.app"),
            ios_store_asset.IOSStore(bundle_id="com.example.ios"),
        ]
    )

    with pytest.raises(ValueError):
        asset.to_proto()


def testMultiAssetToProto_whenUnsupportedTarget_shouldRaiseValueError() -> None:
    asset = multi_asset_asset.MultiAsset(
        targets=[domain_name_asset.DomainName(name="ostorlab.co")]
    )

    with pytest.raises(ValueError):
        asset.to_proto()
