"""Unit tests for ostorlab.scanner.callbacks module."""

from pytest_mock import plugin

from ostorlab.scanner import callbacks

from ostorlab.assets import android_apk
from ostorlab.assets import ipv4
from ostorlab.assets import ipv6
from ostorlab.assets import android_store
from ostorlab.assets import android_aab
from ostorlab.assets import file
from ostorlab.assets import ios_ipa
from ostorlab.assets import domain_name
from ostorlab.assets import link as link_asset
from ostorlab.assets import ios_store
from ostorlab.assets import agent as agent_asset
from ostorlab.scanner.proto.assets import ip_pb2
from ostorlab.scanner.proto.assets import v4_pb2
from ostorlab.scanner.proto.assets import v6_pb2
from ostorlab.scanner.proto.assets import network_pb2
from ostorlab.scanner.proto.assets import link_pb2
from ostorlab.scanner.proto.assets import domain_name_pb2
from ostorlab.scanner.proto.assets import file_pb2
from ostorlab.scanner.proto.assets import android_store_pb2
from ostorlab.scanner.proto.assets import ios_store_pb2
from ostorlab.scanner.proto.assets import ipa_pb2
from ostorlab.scanner.proto.assets import apk_pb2
from ostorlab.scanner.proto.assets import aab_pb2
from ostorlab.scanner.proto.assets import agent_pb2
from ostorlab.scanner.proto.scan._location import startAgentScan_pb2
from ostorlab.scanner import scanner_conf


def testExtractAssets_whenApkAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    """Ensure extract_assets returns correct asset for apk asset."""
    apk_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        apk=apk_pb2.Message(content=b"dummy_apk"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", apk_start_agent_scan_msg, None, registry_conf)

    apk_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(apk_asset, android_apk.AndroidApk) is True
    assert apk_asset.content == b"dummy_apk"
    assert apk_asset.path is None
    assert apk_asset.content_url is None


def testExtractAssets_whenAabAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    """Ensure extract_assets returns correct asset for aab asset."""
    aab_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        aab=aab_pb2.Message(content=b"dummy_aab"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", aab_start_agent_scan_msg, None, registry_conf)

    aab_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(aab_asset, android_aab.AndroidAab) is True
    assert aab_asset.content == b"dummy_aab"
    assert aab_asset.path is None
    assert aab_asset.content_url is None


def testExtractAssets_whenIpaAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    """Ensure extract_assets returns correct asset for ipa asset."""
    ipa_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        ipa=ipa_pb2.Message(content=b"dummy_ipa"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", ipa_start_agent_scan_msg, None, registry_conf)

    ipa_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(ipa_asset, ios_ipa.IOSIpa) is True
    assert ipa_asset.content == b"dummy_ipa"
    assert ipa_asset.path is None
    assert ipa_asset.content_url is None


def testExtractAssets_whenAndroidStoreAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    """Ensure extract_assets returns correct asset for android_store asset."""
    android_store_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        android_store=android_store_pb2.Message(package_name="a.b.c"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan(
        "some_subject", android_store_start_agent_scan_msg, None, registry_conf
    )

    android_store_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(android_store_asset, android_store.AndroidStore) is True
    assert android_store_asset.package_name == "a.b.c"


def testExtractAssets_whenIosStoreAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    """Ensure extract_assets returns correct asset for ios_store asset."""
    ios_store_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        ios_store=ios_store_pb2.Message(bundle_id="a.b.c"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan(
        "some_subject", ios_store_start_agent_scan_msg, None, registry_conf
    )

    ios_store_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(ios_store_asset, ios_store.IOSStore) is True
    assert ios_store_asset.bundle_id == "a.b.c"


def testExtractAssets_whenDomainAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    """Ensure extract_assets returns correct asset for domain asset."""
    domain_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        domain_name=domain_name_pb2.Message(name="ostorlab.co"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan(
        "some_subject", domain_start_agent_scan_msg, None, registry_conf
    )

    domain_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(domain_asset, domain_name.DomainName) is True
    assert domain_asset.name == "ostorlab.co"


def testExtractAssets_whenAgentAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    agent_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        agent=agent_pb2.Message(
            key="agent/ostorlab/agent42",
            version="0.0.1",
            git_location="git@github.com:Ostorlab/agent_42.git",
            yaml_file_location=".",
            docker_location=".",
        ),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan(
        "some_subject", agent_start_agent_scan_msg, None, registry_conf
    )

    agnt_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(agnt_asset, agent_asset.Agent) is True
    assert agnt_asset.key == "agent/ostorlab/agent42"
    assert agnt_asset.version == "0.0.1"
    assert agnt_asset.git_location == "git@github.com:Ostorlab/agent_42.git"
    assert agnt_asset.yaml_file_location == "."
    assert agnt_asset.docker_location == "."


def testExtractAssets_whenFileAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    """Ensure extract_assets returns correct asset for file asset."""
    file_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        file=file_pb2.Message(path="/tmp/dummy_file"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", file_start_agent_scan_msg, None, registry_conf)

    file_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(file_asset, file.File) is True
    assert file_asset.path == "/tmp/dummy_file"
    assert file_asset.content is None
    assert file_asset.content_url is None


def testExtractAssets_whenIpAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    """Ensure extract_assets returns correct asset for ip asset."""
    ip_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        ip=ip_pb2.Message(host="8.8.8.8", version=4),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", ip_start_agent_scan_msg, None, registry_conf)

    ip_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(ip_asset, ipv4.IPv4) is True
    assert ip_asset.host == "8.8.8.8"
    assert ip_asset.version == 4
    # mask is set with ip_network.prefixlen in _prepare_ip_asset
    assert ip_asset.mask == "32"


def testExtractAssets_whenIpv4Asset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    """Ensure extract_assets returns correct asset for ipv4 asset."""
    ipv4_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        ipv4=v4_pb2.Message(host="8.8.8.8", version=4, mask="24"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", ipv4_start_agent_scan_msg, None, registry_conf)

    ipv4_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(ipv4_asset, ipv4.IPv4) is True
    assert ipv4_asset.host == "8.8.8.8"
    assert ipv4_asset.version == 4
    assert ipv4_asset.mask == "24"


def testExtractAssets_whenIpv6WithoutMaskAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    """Ensure extract_assets returns correct asset for ipv6 without mask asset."""
    ipv6_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        ipv6=v6_pb2.Message(host="2001:db8::", version=6),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", ipv6_start_agent_scan_msg, None, registry_conf)

    ipv6_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(ipv6_asset, ipv6.IPv6) is True
    assert ipv6_asset.host == "2001:0db8:0000:0000:0000:0000:0000:0000"
    assert ipv6_asset.version == 6
    # mask is set with ip_network.prefixlen in _prepare_ip_asset
    assert ipv6_asset.mask == "128"


def testExtractAssets_whenIpv6WithMaskAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    """Ensure extract_assets returns correct asset for ipv6 with mask asset."""
    ipv6_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        ipv6=v6_pb2.Message(host="2001:db8::", version=6, mask="64"),
        agents=[],
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", ipv6_start_agent_scan_msg, None, registry_conf)

    ipv6_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(ipv6_asset, ipv6.IPv6) is True
    assert ipv6_asset.host == "2001:0db8:0000:0000:0000:0000:0000:0000"
    assert ipv6_asset.version == 6
    assert ipv6_asset.mask == "64"


def testExtractAssets_whenLinksAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    """Ensure extract_assets returns correct asset for links asset."""
    links_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        links=startAgentScan_pb2.Links(
            links=[
                link_pb2.Message(url="https://ostorlab.co", method="GET"),
                link_pb2.Message(url="https://google.com", method="POST"),
            ]
        ),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan(
        "some_subject", links_start_agent_scan_msg, None, registry_conf
    )

    link_asst1 = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(link_asst1, link_asset.Link) is True
    assert link_asst1.url == "https://ostorlab.co"
    assert link_asst1.method == "GET"
    link_asst2 = runtime_scan_mock.call_args[1].get("assets")[1]
    assert isinstance(link_asst2, link_asset.Link) is True
    assert link_asst2.url == "https://google.com"
    assert link_asst2.method == "POST"


def testExtractAssets_whenNetworkAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
    registry_conf: scanner_conf.RegistryConfig,
) -> None:
    """Ensure extract_assets returns correct asset for network asset."""
    network_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        network=network_pb2.Message(
            ips=[
                ip_pb2.Message(host="8.8.8.8", version=4),
                ip_pb2.Message(host="127.0.0.1", version=4),
                ip_pb2.Message(host="2001:db8::", version=6),
                ip_pb2.Message(host="192.168.1.1", mask="24", version=4),
            ]
        ),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan(
        "some_subject", network_start_agent_scan_msg, None, registry_conf
    )

    ip_asset1 = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(ip_asset1, ipv4.IPv4) is True
    assert ip_asset1.host == "8.8.8.8"
    assert ip_asset1.version == 4
    assert ip_asset1.mask == "32"
    ip_asset2 = runtime_scan_mock.call_args[1].get("assets")[1]
    assert isinstance(ip_asset2, ipv4.IPv4) is True
    assert ip_asset2.host == "127.0.0.1"
    assert ip_asset2.version == 4
    assert ip_asset2.mask == "32"
    ip_asset3 = runtime_scan_mock.call_args[1].get("assets")[2]
    assert isinstance(ip_asset3, ipv6.IPv6) is True
    assert ip_asset3.host == "2001:0db8:0000:0000:0000:0000:0000:0000"
    assert ip_asset3.version == 6
    assert ip_asset3.mask == "128"
    ip_asset4 = runtime_scan_mock.call_args[1].get("assets")[3]
    assert isinstance(ip_asset4, ipv4.IPv4) is True
    assert ip_asset4.host == "192.168.1.1"
    assert ip_asset4.version == 4
    assert ip_asset4.mask == "24"
