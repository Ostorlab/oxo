"""Defines call back to trigger a scan after receiving a startAgentScan messages in the NATS."""

from __future__ import annotations

import logging
import ipaddress
from typing import Any, Callable

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
from ostorlab.agent.message import proto_dict
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


# Maps a single-value asset field name to the asset class built from its dict value.
_SINGLE_ASSET_BUILDERS: dict[str, Callable[..., asset.Asset]] = {
    "android_store": android_store.AndroidStore,
    "ios_store": ios_store.IOSStore,
    "harmonyos_store": harmonyos_store.HarmonyOSStore,
    "ipa": ios_ipa.IOSIpa,
    "apk": android_apk.AndroidApk,
    "aab": android_aab.AndroidAab,
    "harmonyos_hap": harmonyos_hap.HarmonyOSHap,
    "harmonyos_apk": harmonyos_apk.HarmonyOSApk,
    "harmonyos_aab": harmonyos_aab.HarmonyOSAab,
    "harmonyos_rpk": harmonyos_rpk.HarmonyOSRpk,
    "harmonyos_app": harmonyos_app.HarmonyOSApp,
    "domain_name": domain_name.DomainName,
    "agent": agent_asset.Agent,
    "file": file.File,
    "repository": repository_asset.Repository,
    "repository_archive": repository_archive_asset.RepositoryArchive,
}


def _prepare_link_asset(link_value: dict[str, Any]) -> asset.Asset:
    """Return a Link asset from a link proto value dict."""
    return link_asset.Link(
        url=link_value.get("url"),
        method=link_value.get("method") or "GET",
    )


def _prepare_single_asset(
    asset_type: str, asset_value: dict[str, Any], reference_scan_id: int
) -> list[asset.Asset]:
    """Build the injectable assets for a single asset field of a startAgentScan message.

    Args:
        asset_type: Name of the asset field (e.g. "apk", "domain_name", "network").
        asset_value: Dict representation of the asset proto message.
        reference_scan_id: Reference scan id, used for logging unsupported types.

    Returns:
        List of injectable assets for the given field (usually one, more for
        aggregate fields such as "network").
    """
    if asset_type in ("ip", "ipv4", "ipv6"):
        return [_prepare_ip_asset(asset_value)]
    if asset_type == "network":
        return [_prepare_ip_asset(ip) for ip in asset_value.get("ips", [])]
    if asset_type in ("links", "link"):
        links = asset_value.get("links", [asset_value])
        return [_prepare_link_asset(link) for link in links]

    builder = _SINGLE_ASSET_BUILDERS.get(asset_type)
    if builder is None:
        logger.error(
            "%s not supported from scan reference  %s ",
            asset_type,
            reference_scan_id,
        )
        return []
    return [builder(**asset_value)]


def _extract_multi_asset(
    multi_asset_value: dict[str, Any], reference_scan_id: int
) -> list[asset.Asset]:
    """Expand a multi_asset proto value into the flat list of injectable assets."""
    assets: list[asset.Asset] = []
    for asset_type, values in multi_asset_value.items():
        for value in values:
            assets.extend(_prepare_single_asset(asset_type, value, reference_scan_id))
    return assets


def _extract_assets(request: Any) -> list[asset.Asset]:
    """Returns list of specific Ostorlab-injectable assets, from a message received from NATs."""
    logger.debug("Extracting assets.")
    asset_type = request.WhichOneof("asset")
    asset_value = proto_dict.protobuf_to_dict(
        getattr(request, asset_type), use_enum_labels=True
    )
    if asset_type == "multi_asset":
        assets = _extract_multi_asset(asset_value, request.reference_scan_id)
    else:
        assets = _prepare_single_asset(
            asset_type, asset_value, request.reference_scan_id
        )

    logger.debug("Extracted assets: %s.", assets)
    return assets


def _extract_agent_group_definition(request: Any) -> definitions.AgentGroupDefinition:
    agent_group_definition = definitions.AgentGroupDefinition.from_bus_message(request)
    logger.debug("Extracted agent group definition: %s.", agent_group_definition)
    return agent_group_definition


def _extract_scan_id(request: Any) -> int:
    scan_id = int(request.scan_id)
    logger.debug("Extracted scan id: %s.", scan_id)
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
    subject: str,
    request: Any,
    state_reporter: scanner_state_reporter.ScannerStateReporter,
    api_key: str | None = None,
) -> str:
    """Responsible for triggering an Ostorlab scan, after receiving a startAgentScan message in NATs.

    Args:
        subject: Subject of the received message.
        request: Deserialized message.
        state_reporter: State reporter instance responsible for sending current state of the scanner.
        api_key: Optional api key to fetch short-lived download tokens for agent images.
    """
    logger.debug("Triggering scan after receiving message on: %s", subject)
    docker_client = _connect_containers_registry()

    agent_group_definition = _extract_agent_group_definition(request)
    assets = _extract_assets(request)
    scan_id = _extract_scan_id(request)

    state_reporter = _update_state_reporter(state_reporter, scan_id)

    runtime_instance = registry.select_runtime(
        runtime_type="local", scan_id=str(scan_id), run_default_agents=False
    )

    if runtime_instance.can_run(agent_group_definition=agent_group_definition) is True:
        _install_agents(
            runtime_instance=runtime_instance,
            agents=request.agents,
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

        return runtime_instance.name
    else:
        logger.error(
            "The runtime does not support the provided agent list or group definition."
        )
