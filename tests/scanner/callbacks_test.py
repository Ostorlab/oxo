"""Unit tests for ostorlab.scanner.callbacks module."""

import base64

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


def _setup_start_scan_mocks(mocker):
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_mock = mocker.MagicMock()
    runtime_mock.can_run.return_value = True
    mocker.patch(
        "ostorlab.scanner.callbacks.registry.select_runtime", return_value=runtime_mock
    )
    mocker.patch("ostorlab.scanner.callbacks._install_agents")
    return runtime_mock


def testExtractAssets_whenApkAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for apk asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "AndroidApkAssetType",
            "content": base64.b64encode(b"dummy_apk").decode(),
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    apk_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(apk_asset, android_apk.AndroidApk) is True
    assert apk_asset.content == b"dummy_apk"
    assert apk_asset.path is None
    assert apk_asset.content_url is None


def testExtractAssets_whenAabAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for aab asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "AndroidAabAssetType",
            "content": base64.b64encode(b"dummy_aab").decode(),
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    aab_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(aab_asset, android_aab.AndroidAab) is True
    assert aab_asset.content == b"dummy_aab"
    assert aab_asset.path is None
    assert aab_asset.content_url is None


def testExtractAssets_whenIpaAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for ipa asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "IosIpaAssetType",
            "content": base64.b64encode(b"dummy_ipa").decode(),
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    ipa_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(ipa_asset, ios_ipa.IOSIpa) is True
    assert ipa_asset.content == b"dummy_ipa"
    assert ipa_asset.path is None
    assert ipa_asset.content_url is None


def testExtractAssets_whenHarmonyosHapAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for harmonyos hap asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "HarmonyOsHapAssetType",
            "content": base64.b64encode(b"dummy_hap").decode(),
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    hap_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(hap_asset, harmonyos_hap.HarmonyOSHap) is True
    assert hap_asset.content == b"dummy_hap"
    assert hap_asset.path is None
    assert hap_asset.content_url is None


def testExtractAssets_whenHarmonyosApkAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for harmonyos apk asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "HarmonyOsApkAssetType",
            "content": base64.b64encode(b"dummy_hap_apk").decode(),
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    apk_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(apk_asset, harmonyos_apk.HarmonyOSApk) is True
    assert apk_asset.content == b"dummy_hap_apk"
    assert apk_asset.path is None
    assert apk_asset.content_url is None


def testExtractAssets_whenHarmonyosAabAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for harmonyos aab asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "HarmonyOsAabAssetType",
            "content": base64.b64encode(b"dummy_hap_aab").decode(),
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    aab_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(aab_asset, harmonyos_aab.HarmonyOSAab) is True
    assert aab_asset.content == b"dummy_hap_aab"
    assert aab_asset.path is None
    assert aab_asset.content_url is None


def testExtractAssets_whenHarmonyosRpkAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for harmonyos rpk asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "HarmonyOsRpkAssetType",
            "content": base64.b64encode(b"dummy_hap_rpk").decode(),
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    rpk_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(rpk_asset, harmonyos_rpk.HarmonyOSRpk) is True
    assert rpk_asset.content == b"dummy_hap_rpk"
    assert rpk_asset.path is None
    assert rpk_asset.content_url is None


def testExtractAssets_whenHarmonyosAppAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for harmonyos .app asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "HarmonyOsAppAssetType",
            "content": base64.b64encode(b"dummy_hap_app").decode(),
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    app_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(app_asset, harmonyos_app.HarmonyOSApp) is True
    assert app_asset.content == b"dummy_hap_app"
    assert app_asset.path is None
    assert app_asset.content_url is None


def testExtractAssets_whenAndroidStoreAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for android_store asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "AndroidPackageNameAssetType",
            "packageName": "a.b.c",
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    android_store_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(android_store_asset, android_store.AndroidStore) is True
    assert android_store_asset.package_name == "a.b.c"


def testExtractAssets_whenIosStoreAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for ios_store asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "IosBundleIdAssetType",
            "bundleId": "a.b.c",
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    ios_store_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(ios_store_asset, ios_store.IOSStore) is True
    assert ios_store_asset.bundle_id == "a.b.c"


def testExtractAssets_whenHarmonyosStoreAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for harmonyos_store asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "HarmonyOsBundleNameAssetType",
            "bundleName": "com.example.harmony",
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    store_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(store_asset, harmonyos_store.HarmonyOSStore) is True
    assert store_asset.bundle_name == "com.example.harmony"


def testExtractAssets_whenDomainAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for domain asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "DomainNameAssetType",
            "name": "ostorlab.co",
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    domain_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(domain_asset, domain_name.DomainName) is True
    assert domain_asset.name == "ostorlab.co"


def testExtractAssets_whenAgentAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "AgentAssetType",
            "key": "agent/ostorlab/agent42",
            "version": "0.0.1",
            "gitLocation": "git@github.com:Ostorlab/agent_42.git",
            "yamlFileLocation": ".",
            "dockerLocation": ".",
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    agnt_asset = runtime_mock.scan.call_args[1].get("assets")[0]
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
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "FileAssetType",
            "path": "/tmp/dummy_file",
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    file_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(file_asset, file.File) is True
    assert file_asset.path == "/tmp/dummy_file"
    assert file_asset.content is None
    assert file_asset.content_url is None


def testExtractAssets_whenRepositoryAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for repository asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "RepositoryAssetType",
            "repositoryUrl": "https://github.com/org/repo.git",
            "commitHash": "a1a10cdbc6551ba359169a3033f193b7f8c1b95d",
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    extracted_repository_asset = runtime_mock.scan.call_args[1].get("assets")[0]
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
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "RepositoryArchiveAssetType",
            "contentUrl": "https://example.com/source-archive.tar.gz",
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    extracted_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert (
        isinstance(extracted_asset, repository_archive_asset.RepositoryArchive) is True
    )
    assert extracted_asset.content_url == "https://example.com/source-archive.tar.gz"


def testExtractAssets_whenIpAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for ip asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "IpAssetType",
            "host": "8.8.8.8",
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    ip_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(ip_asset, ipv4.IPv4) is True
    assert ip_asset.host == "8.8.8.8"
    assert ip_asset.version == 4
    assert ip_asset.mask == "32"


def testExtractAssets_whenIpv4Asset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for ipv4 asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "Ipv4AssetType",
            "host": "8.8.8.8",
            "mask": "24",
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    ipv4_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(ipv4_asset, ipv4.IPv4) is True
    assert ipv4_asset.host == "8.8.8.8"
    assert ipv4_asset.version == 4
    assert ipv4_asset.mask == "24"


def testExtractAssets_whenIpv6WithoutMaskAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for ipv6 without mask asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "Ipv6AssetType",
            "host": "2001:db8::",
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    ipv6_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(ipv6_asset, ipv6.IPv6) is True
    assert ipv6_asset.host == "2001:0db8:0000:0000:0000:0000:0000:0000"
    assert ipv6_asset.version == 6
    assert ipv6_asset.mask == "128"


def testExtractAssets_whenIpv6WithMaskAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for ipv6 with mask asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "Ipv6AssetType",
            "host": "2001:db8::",
            "mask": "64",
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    ipv6_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(ipv6_asset, ipv6.IPv6) is True
    assert ipv6_asset.host == "2001:0db8:0000:0000:0000:0000:0000:0000"
    assert ipv6_asset.version == 6
    assert ipv6_asset.mask == "64"


def testExtractAssets_whenLinksAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for links asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "UrlAssetType",
            "urls": ["https://ostorlab.co", "https://google.com"],
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    link_asst1 = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(link_asst1, link_asset.Link) is True
    assert link_asst1.url == "https://ostorlab.co"
    assert link_asst1.method == "GET"
    link_asst2 = runtime_mock.scan.call_args[1].get("assets")[1]
    assert isinstance(link_asst2, link_asset.Link) is True
    assert link_asst2.url == "https://google.com"
    assert link_asst2.method == "GET"


def testExtractAssets_whenNetworkAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for network asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {"key": "agentgroup/ostorlab/agent_group42", "agents": []},
        "asset": {
            "__typename": "NetworkAssetType",
            "ips": [
                {"host": "8.8.8.8"},
                {"host": "127.0.0.1"},
                {"host": "2001:db8::"},
                {"host": "192.168.1.1", "mask": "24"},
            ],
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    ip_asset1 = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(ip_asset1, ipv4.IPv4) is True
    assert ip_asset1.host == "8.8.8.8"
    assert ip_asset1.version == 4
    assert ip_asset1.mask == "32"
    ip_asset2 = runtime_mock.scan.call_args[1].get("assets")[1]
    assert isinstance(ip_asset2, ipv4.IPv4) is True
    assert ip_asset2.host == "127.0.0.1"
    assert ip_asset2.version == 4
    assert ip_asset2.mask == "32"
    ip_asset3 = runtime_mock.scan.call_args[1].get("assets")[2]
    assert isinstance(ip_asset3, ipv6.IPv6) is True
    assert ip_asset3.host == "2001:0db8:0000:0000:0000:0000:0000:0000"
    assert ip_asset3.version == 6
    assert ip_asset3.mask == "128"
    ip_asset4 = runtime_mock.scan.call_args[1].get("assets")[3]
    assert isinstance(ip_asset4, ipv4.IPv4) is True
    assert ip_asset4.host == "192.168.1.1"
    assert ip_asset4.version == 4
    assert ip_asset4.mask == "24"


def testStartScan_whenApiKeyProvided_forwardsApiKeyToInstallAgent(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure start_scan forwards the api_key down to install_agent.install
    so the agent image is pulled with a short-lived registry token."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [
                {"key": "agent/ostorlab/agent42", "version": "0.0.1"},
            ],
        },
        "asset": {
            "__typename": "AndroidApkAssetType",
            "content": base64.b64encode(b"dummy_apk").decode(),
        },
    }
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_mock = mocker.MagicMock()
    runtime_mock.can_run.return_value = True
    mocker.patch(
        "ostorlab.scanner.callbacks.registry.select_runtime", return_value=runtime_mock
    )
    install_agent_mock = mocker.patch(
        "ostorlab.scanner.callbacks.install_agent.install"
    )

    state_reporter = mocker.MagicMock()
    callbacks.start_scan(reserved_scan, state_reporter, api_key="test_api_key")

    install_agent_mock.assert_called_once()
    assert install_agent_mock.call_args.kwargs.get("api_key") == "test_api_key"


def testStartScan_whenApiKeyNotProvided_forwardsNoneToInstallAgent(
    mocker: plugin.MockerFixture,
) -> None:
    """When start_scan is invoked without an api_key, install_agent.install
    is called with api_key=None (anonymous pull)."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [
                {"key": "agent/ostorlab/agent42", "version": "0.0.1"},
            ],
        },
        "asset": {
            "__typename": "AndroidApkAssetType",
            "content": base64.b64encode(b"dummy_apk").decode(),
        },
    }
    mocker.patch("ostorlab.scanner.callbacks._connect_containers_registry")
    mocker.patch("ostorlab.scanner.callbacks._update_state_reporter")
    mocker.patch("ostorlab.cli.docker_requirements_checker.init_swarm")
    runtime_mock = mocker.MagicMock()
    runtime_mock.can_run.return_value = True
    mocker.patch(
        "ostorlab.scanner.callbacks.registry.select_runtime", return_value=runtime_mock
    )
    install_agent_mock = mocker.patch(
        "ostorlab.scanner.callbacks.install_agent.install"
    )

    state_reporter = mocker.MagicMock()
    callbacks.start_scan(reserved_scan, state_reporter)

    install_agent_mock.assert_called_once()
    assert install_agent_mock.call_args.kwargs.get("api_key") is None
