"""Unit tests for asset."""

import dataclasses

import pytest

from ostorlab.agent.message import serializer
from ostorlab.assets import asset
from ostorlab.assets import android_apk
from ostorlab.assets import android_aab
from ostorlab.assets import ios_ipa
from ostorlab.assets import ios_testflight
from ostorlab.assets import android_store
from ostorlab.assets import domain_name
from ostorlab.assets import file as file_asset
from ostorlab.assets import api_schema
from ostorlab.assets import agent as agent_asset
from ostorlab.assets import ios_store
from ostorlab.assets import ip as ip_asset
from ostorlab.assets import ipv4 as ipv4_asset
from ostorlab.assets import ipv6 as ipv6_asset
from ostorlab.assets import link as link_asset


def testAssetToProto_whenSelectorIsSetAndCorrect_generatesProto():
    @dataclasses.dataclass
    @asset.selector("v3.asset.file.android.apk")
    class SimpleAndroidApk(asset.Asset):
        content: bytes

    raw = SimpleAndroidApk(b"test").to_proto()
    assert isinstance(raw, bytes)
    unraw = serializer.deserialize("v3.asset.file.android.apk", raw)
    assert unraw.content == b"test"


def testAssetFromDictFactory_withAndroidApkSelector_returnsAndroidApkAsset():
    """Test from_dict_factory returns AndroidApk asset when selector is v3.asset.file.android.apk."""
    data = {"content": b"apk_content", "path": "/path/to/apk"}

    apk_asset = asset.from_dict_factory("v3.asset.file.android.apk", data)

    assert isinstance(apk_asset, android_apk.AndroidApk)
    assert apk_asset == android_apk.AndroidApk(
        content=b"apk_content", path="/path/to/apk"
    )


def testAssetFromDictFactory_withAndroidAabSelector_returnsAndroidAabAsset():
    """Test from_dict_factory returns AndroidAab asset when selector is v3.asset.file.android.aab."""
    data = {"content": b"aab_content", "path": "/path/to/aab"}

    aab_asset = asset.from_dict_factory("v3.asset.file.android.aab", data)

    assert isinstance(aab_asset, android_aab.AndroidAab)
    assert aab_asset == android_aab.AndroidAab(
        content=b"aab_content", path="/path/to/aab"
    )


def testAssetFromDictFactory_withIosIpaSelector_returnsIosIpaAsset():
    """Test from_dict_factory returns IosIpa asset when selector is v3.asset.file.ios.ipa."""
    data = {"content": b"ipa_content", "path": "/path/to/ipa"}

    ipa_asset = asset.from_dict_factory("v3.asset.file.ios.ipa", data)

    assert isinstance(ipa_asset, ios_ipa.IOSIpa)
    assert ipa_asset == ios_ipa.IOSIpa(content=b"ipa_content", path="/path/to/ipa")


def testAssetFromDictFactory_withIosTestflightSelector_returnsIosTestflightAsset():
    """Test from_dict_factory returns IosTestflight asset when selector is v3.asset.file.ios.testflight."""
    data = {"application_url": "http://example.com"}

    ios_testflight_asset = asset.from_dict_factory("v3.asset.file.ios.testflight", data)

    assert isinstance(ios_testflight_asset, ios_testflight.IOSTestflight)
    assert ios_testflight_asset == ios_testflight.IOSTestflight(
        application_url="http://example.com"
    )


def testAssetFromDictFactory_withAndroidStoreSelector_returnsAndroidStoreAsset():
    """Test from_dict_factory returns AndroidStore asset when selector is v3.asset.store.android_store."""
    data = {"package_name": "com.test.app"}

    android_store_asset = asset.from_dict_factory("v3.asset.store.android_store", data)

    assert isinstance(android_store_asset, android_store.AndroidStore)
    assert android_store_asset == android_store.AndroidStore(
        package_name="com.test.app"
    )


def testAssetFromDictFactory_withIosStoreSelector_returnsIosStoreAsset():
    """Test from_dict_factory returns IosStore asset when selector is v3.asset.store.ios_store."""
    data = {"bundle_id": "com.test.app"}

    ios_store_asset = asset.from_dict_factory("v3.asset.store.ios_store", data)

    assert isinstance(ios_store_asset, ios_store.IOSStore)
    assert ios_store_asset == ios_store.IOSStore(bundle_id="com.test.app")


def testAssetFromDictFactory_withDomainNameSelector_returnsDomainNameAsset():
    """Test from_dict_factory returns DomainName asset when selector is v3.asset.domain_name."""
    data = {"name": "ostorlab.co"}

    domain_name_asset = asset.from_dict_factory("v3.asset.domain_name", data)

    assert isinstance(domain_name_asset, domain_name.DomainName)
    assert domain_name_asset == domain_name.DomainName(name="ostorlab.co")


def testAssetFromDictFactory_withFileSelector_returnsFileAsset():
    """Test from_dict_factory returns File asset when selector is v3.asset.file."""
    data = {"content": b"file_content", "path": "/path/to/file"}

    file_asset_obj = asset.from_dict_factory("v3.asset.file", data)

    assert isinstance(file_asset_obj, file_asset.File)
    assert file_asset_obj == file_asset.File(
        content=b"file_content", path="/path/to/file"
    )


def testAssetFromDictFactory_withApiSchemaSelector_returnsApiSchemaAsset():
    """Test from_dict_factory returns ApiSchema asset when selector is v3.asset.file.api_schema."""
    data = {
        "endpoint_url": "http://example.com/api",
        "content": b"schema_content",
        "content_url": "http://example.com/schema",
        "schema_type": "openapi",
    }

    api_schema_asset_obj = asset.from_dict_factory("v3.asset.file.api_schema", data)

    assert isinstance(api_schema_asset_obj, api_schema.ApiSchema)
    assert api_schema_asset_obj == api_schema.ApiSchema(
        endpoint_url="http://example.com/api",
        content=b"schema_content",
        content_url="http://example.com/schema",
        schema_type="openapi",
    )


def testAssetFromDictFactory_withAgentSelector_returnsAgentAsset():
    """Test from_dict_factory returns Agent asset when selector is v3.asset.agent."""
    data = {"key": "agent_key", "version": "1.0.0"}

    agent_asset_obj = asset.from_dict_factory("v3.asset.agent", data)

    assert isinstance(agent_asset_obj, agent_asset.Agent)
    assert agent_asset_obj == agent_asset.Agent(key="agent_key", version="1.0.0")


def testAssetFromDictFactory_withIpSelector_returnsIpAsset():
    """Test from_dict_factory returns IP asset when selector is v3.asset.ip."""
    data = {"host": "127.0.0.1", "version": "4", "mask": "32"}

    ip_asset_obj = asset.from_dict_factory("v3.asset.ip", data)

    assert isinstance(ip_asset_obj, ip_asset.IP)
    assert ip_asset_obj == ip_asset.IP(host="127.0.0.1", version=4, mask="32")


def testAssetFromDictFactory_withIpv4Selector_returnsIpv4Asset():
    """Test from_dict_factory returns IPv4 asset when selector is v3.asset.ip.v4."""
    data = {"host": "127.0.0.1", "mask": "32"}

    ipv4_asset_obj = asset.from_dict_factory("v3.asset.ip.v4", data)

    assert isinstance(ipv4_asset_obj, ipv4_asset.IPv4)
    assert ipv4_asset_obj == ipv4_asset.IPv4(host="127.0.0.1", mask="32")


def testAssetFromDictFactory_withIpv6Selector_returnsIpv6Asset():
    """Test from_dict_factory returns IPv6 asset when selector is v3.asset.ip.v6."""
    data = {"host": "::1", "mask": "128"}

    ipv6_asset_obj = asset.from_dict_factory("v3.asset.ip.v6", data)

    assert isinstance(ipv6_asset_obj, ipv6_asset.IPv6)
    assert ipv6_asset_obj == ipv6_asset.IPv6(host="::1", mask="128")


def testAssetFromDictFactory_withLinkSelector_returnsLinkAsset():
    """Test from_dict_factory returns Link asset when selector is v3.asset.link."""
    data = {"url": "http://example.com", "method": "GET"}

    link_asset_obj = asset.from_dict_factory("v3.asset.link", data)

    assert isinstance(link_asset_obj, link_asset.Link)
    assert link_asset_obj == link_asset.Link(url="http://example.com", method="GET")


def testAssetFromDictFactory_withUnknownSelector_raisesValueError():
    """Test from_dict_factory raises ValueError when selector is unknown."""
    selector = "unknown.selector"

    with pytest.raises(
        ValueError,
        match=f"Could not create asset object due to unknown selector: {selector}",
    ):
        asset.from_dict_factory(selector, {})
