"""Defines call back to trigger a scan after receiving a startAgentScan messages in the NATS."""

from __future__ import annotations

import base64
import logging
import ipaddress
from typing import Any

import docker

from ostorlab.runtimes import registry
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime
from ostorlab.cli import install_agent
from ostorlab.cli import agent_fetcher
from ostorlab.assets import asset
from ostorlab.assets import ipv4
from ostorlab.assets import ipv6
from ostorlab.assets import android_store
from ostorlab.assets import android_aab
from ostorlab.assets import android_apk
from ostorlab.assets import file
from ostorlab.assets import ios_ipa
from ostorlab.assets import harmonyos_hap
from ostorlab.assets import domain_name
from ostorlab.assets import link as link_asset
from ostorlab.assets import ios_store
from ostorlab.assets import agent as agent_asset
from ostorlab.assets import harmonyos_apk
from ostorlab.assets import harmonyos_aab
from ostorlab.assets import harmonyos_rpk
from ostorlab.assets import harmonyos_app
from ostorlab.assets import harmonyos_store
from ostorlab.assets import repository as repository_asset
from ostorlab.assets import repository_archive as repository_archive_asset
from ostorlab.utils import scanner_state_reporter
from ostorlab import exceptions


logger = logging.getLogger(__name__)


def _install_agents(
    runtime_instance: runtime.Runtime,
    agents,
    docker_client: docker.DockerClient | None = None,
    api_key: str | None = None,
) -> None:
    """Trigger installation of the agents that will run the scan."""
    try:
        runtime_instance.install(docker_client=docker_client)
        for agent in agents:
            install_agent.install(
                agent_key=agent.key,
                version=agent.version,
                docker_client=docker_client,
                api_key=api_key,
            )
    except agent_fetcher.AgentDetailsNotFound:
        logger.warning("agent %s not found on the store", agent.key)


def _prepare_ip_asset(ip_asset_value: dict[str, Any]) -> asset.Asset:
    """Return IP assets from ip_asset_value dict."""
    host = ip_asset_value.get("host")
    ip_network = ipaddress.ip_network(host, strict=False)
    if ip_network.version == 4:
        return ipv4.IPv4(
            host=ip_network.network_address.exploded,
            mask=ip_asset_value.get("mask") or str(ip_network.prefixlen),
        )
    elif ip_network.version == 6:
        return ipv6.IPv6(
            host=ip_network.network_address.exploded,
            mask=ip_asset_value.get("mask") or str(ip_network.prefixlen),
        )
    else:
        raise ValueError(f"Invalid Ip address {host}")


def _extract_assets(asset_data: dict[str, Any]) -> list[asset.Asset]:
    """Directly parses a GraphQL asset dictionary into Ostorlab Asset objects."""
    if asset_data is None or asset_data == {}:
        return []

    typename = asset_data.get("__typename")

    kwargs = {k: v for k, v in asset_data.items() if k != "__typename"}

    if "content" in kwargs and isinstance(kwargs["content"], str) is True:
        kwargs["content"] = base64.b64decode(kwargs["content"])

    if typename in ("Ipv4AssetType", "Ipv6AssetType", "IpAssetType"):
        return [_prepare_ip_asset(kwargs)]
    elif typename == "NetworkAssetType":
        return [_prepare_ip_asset(ip) for ip in kwargs.get("ips", [])]
    elif typename == "UrlAssetType":
        return [
            link_asset.Link(url=link, method="GET") for link in kwargs.get("urls", [])
        ]
    elif typename == "AndroidPackageNameAssetType":
        return [android_store.AndroidStore(package_name=kwargs.get("packageName", ""))]
    elif typename == "IosBundleIdAssetType":
        return [ios_store.IOSStore(bundle_id=kwargs.get("bundleId", ""))]
    elif typename == "AndroidAabAssetType":
        return [
            android_aab.AndroidAab(
                content=kwargs.get("content"),
                path=kwargs.get("path"),
                content_url=kwargs.get("contentUrl"),
            )
        ]
    elif typename == "AndroidApkAssetType":
        return [
            android_apk.AndroidApk(
                content=kwargs.get("content"),
                path=kwargs.get("path"),
                content_url=kwargs.get("contentUrl"),
            )
        ]
    elif typename == "IosIpaAssetType":
        return [
            ios_ipa.IOSIpa(
                content=kwargs.get("content"),
                path=kwargs.get("path"),
                content_url=kwargs.get("contentUrl"),
            )
        ]
    elif typename == "FileAssetType":
        return [
            file.File(
                content=kwargs.get("content"),
                path=kwargs.get("path"),
                content_url=kwargs.get("contentUrl"),
            )
        ]
    elif typename == "HarmonyOsBundleNameAssetType":
        return [harmonyos_store.HarmonyOSStore(bundle_name=kwargs.get("bundleName"))]
    elif typename == "HarmonyOsApkAssetType":
        return [
            harmonyos_apk.HarmonyOSApk(
                content=kwargs.get("content"),
                path=kwargs.get("path"),
                content_url=kwargs.get("contentUrl"),
            )
        ]
    elif typename == "HarmonyOsAabAssetType":
        return [
            harmonyos_aab.HarmonyOSAab(
                content=kwargs.get("content"),
                path=kwargs.get("path"),
                content_url=kwargs.get("contentUrl"),
            )
        ]
    elif typename == "HarmonyOsHapAssetType":
        return [
            harmonyos_hap.HarmonyOSHap(
                content=kwargs.get("content"),
                path=kwargs.get("path"),
                content_url=kwargs.get("contentUrl"),
            )
        ]
    elif typename == "HarmonyOsAppAssetType":
        return [
            harmonyos_app.HarmonyOSApp(
                content=kwargs.get("content"),
                path=kwargs.get("path"),
                content_url=kwargs.get("contentUrl"),
            )
        ]
    elif typename == "HarmonyOsRpkAssetType":
        return [
            harmonyos_rpk.HarmonyOSRpk(
                content=kwargs.get("content"),
                path=kwargs.get("path"),
                content_url=kwargs.get("contentUrl"),
            )
        ]
    elif typename == "DomainNameAssetType":
        return [domain_name.DomainName(name=kwargs.get("name", ""))]
    elif typename == "AgentAssetType":
        return [
            agent_asset.Agent(
                key=kwargs.get("key", ""),
                version=kwargs.get("version") or kwargs.get("agentVersion"),
                git_location=kwargs.get("gitLocation"),
                docker_location=kwargs.get("dockerLocation"),
                yaml_file_location=kwargs.get("yamlFileLocation"),
            )
        ]
    elif typename == "RepositoryAssetType":
        return [
            repository_asset.Repository(
                repository_url=kwargs.get("repositoryUrl", ""),
                commit_hash=kwargs.get("commitHash", ""),
                provider=kwargs.get("provider", ""),
            )
        ]
    elif typename == "RepositoryArchiveAssetType":
        return [
            repository_archive_asset.RepositoryArchive(
                content=kwargs.get("content"),
                path=kwargs.get("path"),
                content_url=kwargs.get("contentUrl"),
            )
        ]
    else:
        logger.error("%s not supported from scan asset payload", typename)
        return []


def _extract_agent_group_definition(
    request: dict[str, Any],
) -> definitions.AgentGroupDefinition:
    agent_group_definition = definitions.AgentGroupDefinition.from_api_response(request)
    logger.info("Extracted agent group definition: %s.", agent_group_definition)
    return agent_group_definition


def _extract_scan_id(request: dict[str, Any]) -> int:
    scan_id = int(request.get("id", 0))
    logger.info("Extracted scan id: %s.", scan_id)
    return scan_id


def _update_state_reporter(
    state_reporter: scanner_state_reporter.ScannerStateReporter, scan_id: int
) -> scanner_state_reporter.ScannerStateReporter:
    state_reporter.scan_id = scan_id
    return state_reporter


def _connect_containers_registry() -> docker.DockerClient:
    """Build a docker client for pulling agent images.

    Authentication is handled per-pull via a short-lived token in install_agent,
    so no registry login is performed here.
    """
    logger.debug("Creating docker client for private container registry.")
    return docker.from_env()


def start_scan(
    request: dict[str, Any],
    state_reporter: scanner_state_reporter.ScannerStateReporter,
    api_key: str | None = None,
) -> str:
    """Responsible for triggering an Ostorlab scan, after receiving a scan from the API.

    Args:
        request: API response data for the scan.
        state_reporter: State reporter instance responsible for sending current state of the scanner.
        api_key: Optional api key to fetch short-lived download tokens for agent images.
    """
    logger.debug("Triggering scan after receiving scan from API")
    docker_client = _connect_containers_registry()

    agent_group_definition = _extract_agent_group_definition(request.get("agentGroup"))
    assets = _extract_assets(request.get("asset"))
    scan_id = _extract_scan_id(request)

    state_reporter = _update_state_reporter(state_reporter, scan_id)

    runtime_instance = registry.select_runtime(
        runtime_type="local", scan_id=str(scan_id), run_default_agents=False
    )

    if runtime_instance.can_run(agent_group_definition=agent_group_definition) is True:
        _install_agents(
            runtime_instance=runtime_instance,
            agents=agent_group_definition.agents,
            docker_client=docker_client,
            api_key=api_key,
        )

        try:
            runtime_instance.scan(
                agent_group_definition=agent_group_definition,
                assets=assets,
                title=None,
            )
        except exceptions.OstorlabError as e:
            logger.error(f"An error was encountered while running the scan: {e}")
            raise

        return runtime_instance.name
    else:
        logger.error(
            "The runtime does not support the provided agent list or group definition."
        )
