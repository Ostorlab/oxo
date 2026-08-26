"""Unit tests for ostorlab.scanner.callbacks module."""

import base64

import pytest
from pytest_mock import plugin

from ostorlab.agent.schema import validator
from ostorlab.assets import agent as agent_asset
from ostorlab.assets import (
    android_aab,
    android_apk,
    android_store,
    domain_name,
    file,
    harmonyos_aab,
    harmonyos_apk,
    harmonyos_app,
    harmonyos_hap,
    harmonyos_rpk,
    harmonyos_store,
    ios_ipa,
    ios_store,
    ipv4,
    ipv6,
)
from ostorlab.assets import link as link_asset
from ostorlab.assets import multi_asset as multi_asset_asset
from ostorlab.assets import repository as repository_asset
from ostorlab.assets import repository_archive as repository_archive_asset
from ostorlab.assets import risk as risk_asset
from ostorlab.assets import ticket as ticket_asset
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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


def testStartScan_whenGcpCredentialProvided_forwardsItToLocalRuntime(
    mocker: plugin.MockerFixture,
) -> None:
    """Forward GCP logging credentials to the local runtime."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
        "asset": {
            "__typename": "AndroidApkAssetType",
            "content": base64.b64encode(b"dummy_apk").decode(),
        },
    }
    mocker.patch("ostorlab.scanner.callbacks.docker.from_env")
    mocker.patch("ostorlab.scanner.callbacks.install_agent.install")
    runtime_mock = mocker.MagicMock()
    runtime_mock.can_run.return_value = True
    select_runtime_mock = mocker.patch(
        "ostorlab.scanner.callbacks.registry.select_runtime",
        return_value=runtime_mock,
    )
    callbacks.start_scan(
        reserved_scan,
        mocker.MagicMock(),
        gcp_logging_credential="gcp-credential",
    )

    select_runtime_mock.assert_called_once_with(
        runtime_type="local",
        scan_id="42",
        run_default_agents=False,
        gcp_logging_credential="gcp-credential",
    )


def testExtractAssets_whenAabAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for aab asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
        "asset": {
            "__typename": "RepositoryAssetType",
            "repositoryUrl": "https://github.com/org/repo.git",
            "commitHash": "a1a10cdbc6551ba359169a3033f193b7f8c1b95d",
            "provider": "GITHUB",
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
    assert extracted_repository_asset.provider == "GITHUB"


def testExtractAssets_whenRiskAssetWithRepositoryTarget_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets maps a repository target onto a risk asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
        "asset": {
            "__typename": "RiskAssetType",
            "description": "Vulnerable dependency",
            "rating": "MEDIUM",
            "target": {
                "__typename": "RepositoryAssetType",
                "repositoryUrl": "https://github.com/org/repo.git",
                "commitHash": "a1a10cdbc6551ba359169a3033f193b7f8c1b95d",
                "provider": "GITLAB",
            },
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    extracted_risk_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(extracted_risk_asset, risk_asset.Risk) is True
    assert extracted_risk_asset.description == "Vulnerable dependency"
    assert extracted_risk_asset.rating == "MEDIUM"
    assert (
        isinstance(extracted_risk_asset.repository, repository_asset.Repository) is True
    )
    assert (
        extracted_risk_asset.repository.repository_url
        == "https://github.com/org/repo.git"
    )
    assert (
        extracted_risk_asset.repository.commit_hash
        == "a1a10cdbc6551ba359169a3033f193b7f8c1b95d"
    )
    assert extracted_risk_asset.repository.provider == "GITLAB"


def testExtractAssets_whenRepositoryArchiveAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for repository archive asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
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
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
        "asset": {
            "__typename": "NetworkAssetType",
            "networks": ["18.2.46.129/32", "13.8.98.58/32"],
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    ip_asset1 = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(ip_asset1, ipv4.IPv4) is True
    assert ip_asset1.host == "18.2.46.129"
    assert ip_asset1.version == 4
    assert ip_asset1.mask == "32"
    ip_asset2 = runtime_mock.scan.call_args[1].get("assets")[1]
    assert isinstance(ip_asset2, ipv4.IPv4) is True
    assert ip_asset2.host == "13.8.98.58"
    assert ip_asset2.version == 4
    assert ip_asset2.mask == "32"


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


def testExtractAssets_whenRiskAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for risk asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
        "asset": {
            "__typename": "RiskAssetType",
            "description": "Exposed server",
            "rating": "HIGH",
            "target": {
                "__typename": "Ipv4AssetType",
                "host": "8.8.8.8",
                "mask": "32",
            },
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    extracted_risk_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(extracted_risk_asset, risk_asset.Risk) is True
    assert extracted_risk_asset.description == "Exposed server"
    assert extracted_risk_asset.rating == "HIGH"
    assert extracted_risk_asset.ipv4 is not None
    assert extracted_risk_asset.ipv4.host == "8.8.8.8"
    assert extracted_risk_asset.ipv4.mask == "32"


def testExtractAssets_whenTicketAsset_shouldReturnCorrectAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct asset for ticket asset."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
        "asset": {
            "__typename": "TicketAssetType",
            "title": "Test Ticket",
            "description": "This is a test ticket",
            "ticketId": "123",
            "ticketKey": "TICKET-123",
            "ticketComments": [
                {"author": "sec-ops", "value": "confirmed reproduction"},
                {"author": "dev-team", "value": "fix in progress"},
            ],
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    extracted_ticket_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(extracted_ticket_asset, ticket_asset.Ticket) is True
    assert extracted_ticket_asset.title == "Test Ticket"
    assert extracted_ticket_asset.description == "This is a test ticket"
    assert extracted_ticket_asset.ticket_id == "123"
    assert extracted_ticket_asset.ticket_key == "TICKET-123"
    assert len(extracted_ticket_asset.comments) == 2
    assert extracted_ticket_asset.comments[0].author == "sec-ops"
    assert extracted_ticket_asset.comments[0].message == "confirmed reproduction"
    assert extracted_ticket_asset.comments[1].author == "dev-team"
    assert extracted_ticket_asset.comments[1].message == "fix in progress"


def testExtractAssets_whenRisksAsset_shouldReturnCorrectAssets(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns correct assets for risks asset (plural)."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
        "asset": {
            "__typename": "RisksAssetType",
            "risks": [
                {
                    "description": "Exposed server",
                    "rating": "HIGH",
                    "target": {
                        "__typename": "Ipv4AssetType",
                        "host": "8.8.8.8",
                        "mask": "32",
                    },
                },
                {
                    "description": "Weak password",
                    "rating": "MEDIUM",
                    "target": {
                        "__typename": "DomainNameAssetType",
                        "name": "example.com",
                    },
                },
            ],
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    assets = runtime_mock.scan.call_args[1].get("assets")
    assert len(assets) == 2

    assert isinstance(assets[0], risk_asset.Risk) is True
    assert assets[0].description == "Exposed server"
    assert assets[0].rating == "HIGH"
    assert assets[0].ipv4 is not None
    assert assets[0].ipv4.host == "8.8.8.8"

    assert isinstance(assets[1], risk_asset.Risk) is True
    assert assets[1].description == "Weak password"
    assert assets[1].rating == "MEDIUM"
    assert assets[1].domain_name is not None
    assert assets[1].domain_name.name == "example.com"


def testExtractAssets_whenMultiAsset_shouldReturnOneMultiAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure extract_assets returns one multi asset holding every member."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
        "asset": {
            "__typename": "MultiAssetsAssetType",
            "files": [
                {
                    "__typename": "FileAssetType",
                    "path": "/tmp/dump.bin",
                    "contentUrl": "https://storage.co/dump.bin",
                }
            ],
            "androidApk": {
                "__typename": "AndroidApkAssetType",
                "path": "/tmp/app.apk",
                "contentUrl": "https://storage.co/app.apk",
            },
            "repositories": [
                {
                    "__typename": "RepositoryAssetType",
                    "provider": "github",
                    "repositoryUrl": "https://github.com/Ostorlab/oxo",
                    "commitHash": "deadbeef",
                }
            ],
            "repositoryArchives": [
                {
                    "__typename": "RepositoryArchiveAssetType",
                    "path": "/tmp/archive.zip",
                    "contentUrl": "https://storage.co/archive.zip",
                }
            ],
            "urls": [
                {
                    "__typename": "UrlAssetType",
                    "urls": ["https://ostorlab.co", "https://google.com"],
                }
            ],
            "ips": [
                {
                    "__typename": "IpAssetType",
                    "host": "8.8.8.8",
                    "version": 4,
                    "mask": "32",
                }
            ],
            "ipv4s": [
                {
                    "__typename": "Ipv4AssetType",
                    "host": "192.168.1.1",
                    "version": 4,
                    "mask": "24",
                }
            ],
            "ipv6s": [
                {
                    "__typename": "Ipv6AssetType",
                    "host": "2001:db8::",
                    "version": 6,
                    "mask": "64",
                }
            ],
            "apiSchemas": [
                {
                    "endpointUrl": "https://ostorlab.co/v1",
                    "contentUrl": "https://storage.co/openapi.json",
                }
            ],
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    assets = runtime_mock.scan.call_args[1].get("assets")
    assert len(assets) == 1
    multi_asset = assets[0]
    assert isinstance(multi_asset, multi_asset_asset.MultiAsset) is True
    assert multi_asset.android_apk.path == "/tmp/app.apk"
    assert [file_member.path for file_member in multi_asset.files] == ["/tmp/dump.bin"]
    assert [repository.repository_url for repository in multi_asset.repositories] == [
        "https://github.com/Ostorlab/oxo"
    ]
    assert [archive.path for archive in multi_asset.repository_archives] == [
        "/tmp/archive.zip"
    ]
    assert [url.url for url in multi_asset.urls] == [
        "https://ostorlab.co",
        "https://google.com",
    ]
    assert [(ip.host, ip.mask) for ip in multi_asset.ipv4s] == [
        ("8.8.8.8", "32"),
        ("192.168.1.1", "24"),
    ]
    assert [ip.host for ip in multi_asset.ipv6s] == [
        "2001:0db8:0000:0000:0000:0000:0000:0000"
    ]
    assert [
        (schema.endpoint_url, schema.content_url) for schema in multi_asset.api_schemas
    ] == [("https://ostorlab.co/v1", "https://storage.co/openapi.json")]


def testExtractAssets_whenMultiAssetWithStoreMember_shouldReturnStoreAsMobileMember(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure a store member of a multi asset lands on its mobile field."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
        "asset": {
            "__typename": "MultiAssetsAssetType",
            "androidPackageName": {
                "__typename": "AndroidPackageNameAssetType",
                "packageName": "com.ostorlab.app",
            },
            "urls": [{"__typename": "UrlAssetType", "urls": ["https://ostorlab.co"]}],
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    multi_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert isinstance(multi_asset, multi_asset_asset.MultiAsset) is True
    assert multi_asset.android_store.package_name == "com.ostorlab.app"
    assert multi_asset.android_apk is None


def testExtractAssets_whenMultiAssetWithTwoMobileMembers_shouldRaiseValidationError(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure a multi asset with two mobile members is rejected, since the proto oneof
    would silently drop one of them."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
        "asset": {
            "__typename": "MultiAssetsAssetType",
            "androidApk": {
                "__typename": "AndroidApkAssetType",
                "path": "/tmp/app.apk",
            },
            "iosIpa": {"__typename": "IosIpaAssetType", "path": "/tmp/app.ipa"},
        },
    }
    _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    with pytest.raises(validator.ValidationError):
        callbacks.start_scan(reserved_scan, state_reporter)


def testExtractAssets_whenMultiAssetApiSchemaHasNoEndpointUrl_shouldSkipIt(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure an api schema with no endpoint url is skipped rather than failing the scan."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
        "asset": {
            "__typename": "MultiAssetsAssetType",
            "urls": [{"__typename": "UrlAssetType", "urls": ["https://ostorlab.co"]}],
            "apiSchemas": [
                {"endpointUrl": None, "contentUrl": "https://storage.co/openapi.json"}
            ],
        },
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    multi_asset = runtime_mock.scan.call_args[1].get("assets")[0]
    assert multi_asset.api_schemas == []
    assert [url.url for url in multi_asset.urls] == ["https://ostorlab.co"]


def testExtractAssets_whenMultiAssetWithNoMember_shouldReturnNoAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure an empty multi asset payload injects no empty message."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
        "asset": {"__typename": "MultiAssetsAssetType", "androidApk": None},
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    assert runtime_mock.scan.call_args[1].get("assets") is None


def testStartScan_whenNoAssetExtracted_shouldPassNoneToRuntime(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure an unresolved asset injects nothing rather than an empty asset volume."""
    reserved_scan = {
        "id": 42,
        "agentGroup": {
            "key": "agentgroup/ostorlab/agent_group42",
            "agents": [{"key": "agent/ostorlab/dummy"}],
        },
        "asset": {"__typename": "UnknownAssetType"},
    }
    runtime_mock = _setup_start_scan_mocks(mocker)
    state_reporter = mocker.MagicMock()

    callbacks.start_scan(reserved_scan, state_reporter)

    assert runtime_mock.scan.call_args[1].get("assets") is None
