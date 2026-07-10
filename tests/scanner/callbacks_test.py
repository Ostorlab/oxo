"""Unit tests for ostorlab.scanner.callbacks module."""

from pytest_mock import plugin

from ostorlab.assets import agent as agent_asset
from ostorlab.assets import android_aab
from ostorlab.assets import android_apk
from ostorlab.assets import android_store
from ostorlab.assets import domain_name
from ostorlab.assets import file
from ostorlab.assets import harmonyos_hap
from ostorlab.assets import harmonyos_apk
from ostorlab.assets import harmonyos_aab
from ostorlab.assets import harmonyos_rpk
from ostorlab.assets import harmonyos_app
from ostorlab.assets import harmonyos_store
from ostorlab.assets import ios_ipa
from ostorlab.assets import ios_store
from ostorlab.assets import ipv4
from ostorlab.assets import ipv6
from ostorlab.assets import link as link_asset
from ostorlab.assets import repository as repository_asset
from ostorlab.assets import repository_archive as repository_archive_asset
from ostorlab.scanner import callbacks
from ostorlab.scanner.proto.assets import aab_pb2
from ostorlab.scanner.proto.assets import agent_pb2
from ostorlab.scanner.proto.assets import android_store_pb2
from ostorlab.scanner.proto.assets import apk_pb2
from ostorlab.scanner.proto.assets import domain_name_pb2
from ostorlab.scanner.proto.assets import file_pb2
from ostorlab.scanner.proto.assets import harmonyos_hap_pb2
from ostorlab.scanner.proto.assets import harmonyos_apk_pb2
from ostorlab.scanner.proto.assets import harmonyos_aab_pb2
from ostorlab.scanner.proto.assets import harmonyos_rpk_pb2
from ostorlab.scanner.proto.assets import harmonyos_app_pb2
from ostorlab.scanner.proto.assets import harmonyos_store_pb2
from ostorlab.scanner.proto.assets import ios_store_pb2
from ostorlab.scanner.proto.assets import ip_pb2
from ostorlab.scanner.proto.assets import ipa_pb2
from ostorlab.scanner.proto.assets import link_pb2
from ostorlab.scanner.proto.assets import multi_asset_pb2
from ostorlab.scanner.proto.assets import network_pb2
from ostorlab.scanner.proto.assets import repository_pb2
from ostorlab.scanner.proto.assets import repository_archive_pb2
from ostorlab.scanner.proto.assets import v4_pb2
from ostorlab.scanner.proto.assets import v6_pb2
from ostorlab.scanner.proto.scan._location import startAgentScan_pb2


def testExtractAssets_whenApkAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", apk_start_agent_scan_msg, None)

    apk_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(apk_asset, android_apk.AndroidApk) is True
    assert apk_asset.content == b"dummy_apk"
    assert apk_asset.path is None
    assert apk_asset.content_url is None


def testExtractAssets_whenAabAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", aab_start_agent_scan_msg, None)

    aab_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(aab_asset, android_aab.AndroidAab) is True
    assert aab_asset.content == b"dummy_aab"
    assert aab_asset.path is None
    assert aab_asset.content_url is None


def testExtractAssets_whenIpaAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", ipa_start_agent_scan_msg, None)

    ipa_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(ipa_asset, ios_ipa.IOSIpa) is True
    assert ipa_asset.content == b"dummy_ipa"
    assert ipa_asset.path is None
    assert ipa_asset.content_url is None


def testExtractAssets_whenHarmonyosHapAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for harmonyos hap asset."""
    hap_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        harmonyos_hap=harmonyos_hap_pb2.Message(content=b"dummy_hap"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", hap_start_agent_scan_msg, None)

    hap_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(hap_asset, harmonyos_hap.HarmonyOSHap) is True
    assert hap_asset.content == b"dummy_hap"
    assert hap_asset.path is None
    assert hap_asset.content_url is None


def testExtractAssets_whenHarmonyosApkAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for harmonyos apk asset."""
    apk_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        harmonyos_apk=harmonyos_apk_pb2.Message(content=b"dummy_hap_apk"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", apk_start_agent_scan_msg, None)

    apk_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(apk_asset, harmonyos_apk.HarmonyOSApk) is True
    assert apk_asset.content == b"dummy_hap_apk"
    assert apk_asset.path is None
    assert apk_asset.content_url is None


def testExtractAssets_whenHarmonyosAabAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for harmonyos aab asset."""
    aab_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        harmonyos_aab=harmonyos_aab_pb2.Message(content=b"dummy_hap_aab"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", aab_start_agent_scan_msg, None)

    aab_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(aab_asset, harmonyos_aab.HarmonyOSAab) is True
    assert aab_asset.content == b"dummy_hap_aab"
    assert aab_asset.path is None
    assert aab_asset.content_url is None


def testExtractAssets_whenHarmonyosRpkAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for harmonyos rpk asset."""
    rpk_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        harmonyos_rpk=harmonyos_rpk_pb2.Message(content=b"dummy_hap_rpk"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", rpk_start_agent_scan_msg, None)

    rpk_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(rpk_asset, harmonyos_rpk.HarmonyOSRpk) is True
    assert rpk_asset.content == b"dummy_hap_rpk"
    assert rpk_asset.path is None
    assert rpk_asset.content_url is None


def testExtractAssets_whenHarmonyosAppAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for harmonyos .app asset."""
    app_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        harmonyos_app=harmonyos_app_pb2.Message(content=b"dummy_hap_app"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", app_start_agent_scan_msg, None)

    app_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(app_asset, harmonyos_app.HarmonyOSApp) is True
    assert app_asset.content == b"dummy_hap_app"
    assert app_asset.path is None
    assert app_asset.content_url is None


def testExtractAssets_whenAndroidStoreAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", android_store_start_agent_scan_msg, None)

    android_store_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(android_store_asset, android_store.AndroidStore) is True
    assert android_store_asset.package_name == "a.b.c"


def testExtractAssets_whenIosStoreAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", ios_store_start_agent_scan_msg, None)

    ios_store_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(ios_store_asset, ios_store.IOSStore) is True
    assert ios_store_asset.bundle_id == "a.b.c"


def testExtractAssets_whenHarmonyosStoreAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for harmonyos_store asset."""
    harmonyos_store_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        harmonyos_store=harmonyos_store_pb2.Message(bundle_name="com.example.harmony"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", harmonyos_store_start_agent_scan_msg, None)

    store_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(store_asset, harmonyos_store.HarmonyOSStore) is True
    assert store_asset.bundle_name == "com.example.harmony"


def testExtractAssets_whenDomainAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", domain_start_agent_scan_msg, None)

    domain_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(domain_asset, domain_name.DomainName) is True
    assert domain_asset.name == "ostorlab.co"


def testExtractAssets_whenAgentAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", agent_start_agent_scan_msg, None)

    agnt_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(agnt_asset, agent_asset.Agent) is True
    assert agnt_asset.key == "agent/ostorlab/agent42"
    assert agnt_asset.version == "0.0.1"
    assert agnt_asset.git_location == "git@github.com:Ostorlab/agent_42.git"
    assert agnt_asset.yaml_file_location == "."
    assert agnt_asset.docker_location == "."


def testExtractAssets_whenFileAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", file_start_agent_scan_msg, None)

    file_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(file_asset, file.File) is True
    assert file_asset.path == "/tmp/dummy_file"
    assert file_asset.content is None
    assert file_asset.content_url is None


def testExtractAssets_whenRepositoryAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for repository asset."""
    repository_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        repository=repository_pb2.Message(
            repository_url="https://github.com/org/repo.git",
            commit_hash="a1a10cdbc6551ba359169a3033f193b7f8c1b95d",
        ),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", repository_start_agent_scan_msg, None)

    extracted_repository_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(extracted_repository_asset, repository_asset.Repository) is True
    assert (
        extracted_repository_asset.repository_url == "https://github.com/org/repo.git"
    )
    assert (
        extracted_repository_asset.commit_hash
        == "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"
    )


def testExtractAssets_whenRepositoryArchiveAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for repository archive asset."""
    repository_archive_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        repository_archive=repository_archive_pb2.Message(
            content_url="https://example.com/source-archive.tar.gz",
        ),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", repository_archive_start_agent_scan_msg, None)

    extracted_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert (
        isinstance(extracted_asset, repository_archive_asset.RepositoryArchive) is True
    )
    assert extracted_asset.content_url == "https://example.com/source-archive.tar.gz"


def testExtractAssets_whenIpAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", ip_start_agent_scan_msg, None)

    ip_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(ip_asset, ipv4.IPv4) is True
    assert ip_asset.host == "8.8.8.8"
    assert ip_asset.version == 4
    # mask is set with ip_network.prefixlen in _prepare_ip_asset
    assert ip_asset.mask == "32"


def testExtractAssets_whenIpv4Asset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", ipv4_start_agent_scan_msg, None)

    ipv4_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(ipv4_asset, ipv4.IPv4) is True
    assert ipv4_asset.host == "8.8.8.8"
    assert ipv4_asset.version == 4
    assert ipv4_asset.mask == "24"


def testExtractAssets_whenIpv6WithoutMaskAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", ipv6_start_agent_scan_msg, None)

    ipv6_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(ipv6_asset, ipv6.IPv6) is True
    assert ipv6_asset.host == "2001:0db8:0000:0000:0000:0000:0000:0000"
    assert ipv6_asset.version == 6
    # mask is set with ip_network.prefixlen in _prepare_ip_asset
    assert ipv6_asset.mask == "128"


def testExtractAssets_whenIpv6WithMaskAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", ipv6_start_agent_scan_msg, None)

    ipv6_asset = runtime_scan_mock.call_args[1].get("assets")[0]
    assert isinstance(ipv6_asset, ipv6.IPv6) is True
    assert ipv6_asset.host == "2001:0db8:0000:0000:0000:0000:0000:0000"
    assert ipv6_asset.version == 6
    assert ipv6_asset.mask == "64"


def testExtractAssets_whenLinksAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", links_start_agent_scan_msg, None)

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
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", network_start_agent_scan_msg, None)

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


def testStartScan_whenApiKeyProvided_forwardsApiKeyToInstallAgent(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure start_scan forwards the api_key down to install_agent.install
    so the agent image is pulled with a short-lived registry token."""
    start_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[
            startAgentScan_pb2.Agent(
                key="agent/ostorlab/agent42",
                version="0.0.1",
            )
        ],
        apk=apk_pb2.Message(content=b"dummy_apk"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime.scan")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime.install")
    install_agent_mock = mocker.patch(
        "ostorlab.scanner.callbacks.install_agent.install"
    )

    callbacks.start_scan(
        "some_subject",
        start_scan_msg,
        None,
        api_key="test_api_key",
    )

    install_agent_mock.assert_called_once()
    assert install_agent_mock.call_args.kwargs.get("api_key") == "test_api_key"


def testStartScan_whenApiKeyNotProvided_forwardsNoneToInstallAgent(
    mocker: plugin.MockerFixture,
) -> None:
    """When start_scan is invoked without an api_key, install_agent.install
    is called with api_key=None (anonymous pull)."""
    start_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[
            startAgentScan_pb2.Agent(
                key="agent/ostorlab/agent42",
                version="0.0.1",
            )
        ],
        apk=apk_pb2.Message(content=b"dummy_apk"),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime.scan")
    mocker.patch("ostorlab.runtimes.local.runtime.LocalRuntime.install")
    install_agent_mock = mocker.patch(
        "ostorlab.scanner.callbacks.install_agent.install"
    )

    callbacks.start_scan("some_subject", start_scan_msg, None)

    install_agent_mock.assert_called_once()
    assert install_agent_mock.call_args.kwargs.get("api_key") is None


def testExtractAssets_whenMultiAsset_shouldReturnAllComposedAssets(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets expands a multi_asset message into every composed asset."""
    multi_asset_start_agent_scan_msg = startAgentScan_pb2.Message(
        reference_scan_id=42,
        key="agentgroup/ostorlab/agent_group42",
        agents=[],
        multi_asset=multi_asset_pb2.Message(
            apk=[
                apk_pb2.Message(content_url="https://cdn.example.com/app.apk"),
                apk_pb2.Message(content_url="https://cdn.example.com/second-app.apk"),
            ],
            ipa=[ipa_pb2.Message(content_url="https://cdn.example.com/app.ipa")],
            harmonyos_hap=[
                harmonyos_hap_pb2.Message(content_url="https://cdn.example.com/app.hap")
            ],
            domain_name=[domain_name_pb2.Message(name="example.com")],
            link=[link_pb2.Message(url="https://app.example.com", method="GET")],
            repository=[
                repository_pb2.Message(
                    repository_url="https://github.com/org/repo",
                    commit_hash="deadbeef",
                )
            ],
            file=[file_pb2.Message(content_url="https://cdn.example.com/source.zip")],
        ),
    )
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_scan_mock = mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.scan"
    )

    callbacks.start_scan("some_subject", multi_asset_start_agent_scan_msg, None)

    scanned_assets = runtime_scan_mock.call_args[1].get("assets")
    assert len(scanned_assets) == 8
    apk_urls = [
        a.content_url
        for a in scanned_assets
        if isinstance(a, android_apk.AndroidApk) is True
    ]
    assert apk_urls == [
        "https://cdn.example.com/app.apk",
        "https://cdn.example.com/second-app.apk",
    ]
    assert any(isinstance(a, ios_ipa.IOSIpa) is True for a in scanned_assets) is True
    assert (
        any(isinstance(a, domain_name.DomainName) is True for a in scanned_assets)
        is True
    )
    assert any(isinstance(a, link_asset.Link) is True for a in scanned_assets) is True
    assert (
        any(isinstance(a, repository_asset.Repository) is True for a in scanned_assets)
        is True
    )
    assert any(isinstance(a, file.File) is True for a in scanned_assets) is True
