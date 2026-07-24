"""Defines call back to trigger a scan after receiving a startAgentScan messages in the NATS."""

from __future__ import annotations

import ipaddress
import logging
from typing import Any

import docker

from ostorlab import exceptions
from ostorlab.agent.message import proto_dict
from ostorlab.assets import agent as agent_asset
from ostorlab.assets import (
    android_aab,
    android_apk,
    android_store,
    asset,
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
from ostorlab.assets import repository as repository_asset
from ostorlab.assets import repository_archive as repository_archive_asset
from ostorlab.cli import agent_fetcher, install_agent
from ostorlab.runtimes import definitions, registry, runtime
from ostorlab.utils import scanner_state_reporter

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


def _extract_assets(request: Any) -> list[asset.Asset]:
    """Returns list of specific Ostorlab-injectable assets, from a message received from NATs."""
    logger.debug("Extracting assets.")
    assets = []
    asset_type = request.WhichOneof("asset")
    asset_value = proto_dict.protobuf_to_dict(
        getattr(request, asset_type), use_enum_labels=True
    )
    if asset_type in ("ip", "ipv4", "ipv6"):
        assets.append(_prepare_ip_asset(asset_value))
    elif asset_type == "android_store":
        assets.append(android_store.AndroidStore(**asset_value))
    elif asset_type == "ios_store":
        assets.append(ios_store.IOSStore(**asset_value))
    elif asset_type == "harmonyos_store":
        assets.append(harmonyos_store.HarmonyOSStore(**asset_value))
    elif asset_type == "ipa":
        assets.append(ios_ipa.IOSIpa(**asset_value))
    elif asset_type == "apk":
        assets.append(android_apk.AndroidApk(**asset_value))
    elif asset_type == "aab":
        assets.append(android_aab.AndroidAab(**asset_value))
    elif asset_type == "harmonyos_hap":
        assets.append(harmonyos_hap.HarmonyOSHap(**asset_value))
    elif asset_type == "harmonyos_apk":
        assets.append(harmonyos_apk.HarmonyOSApk(**asset_value))
    elif asset_type == "harmonyos_aab":
        assets.append(harmonyos_aab.HarmonyOSAab(**asset_value))
    elif asset_type == "harmonyos_rpk":
        assets.append(harmonyos_rpk.HarmonyOSRpk(**asset_value))
    elif asset_type == "harmonyos_app":
        assets.append(harmonyos_app.HarmonyOSApp(**asset_value))
    elif asset_type == "domain_name":
        assets.append(domain_name.DomainName(**asset_value))
    elif asset_type == "agent":
        assets.append(agent_asset.Agent(**asset_value))
    elif asset_type == "file":
        assets.append(file.File(**asset_value))
    elif asset_type == "repository":
        assets.append(repository_asset.Repository(**asset_value))
    elif asset_type == "repository_archive":
        assets.append(repository_archive_asset.RepositoryArchive(**asset_value))
    elif asset_type == "network":
        for ip in asset_value.get("ips"):
            ip_asset = _prepare_ip_asset(ip)
            assets.append(ip_asset)
    elif asset_type == "links":
        for link in asset_value.get("links"):
            assets.append(
                link_asset.Link(
                    url=link.get("url"),
                    method=link.get("method") or "GET",
                )
            )

    else:
        logger.error(
            "%s not supported from scan reference  %s ",
            asset_type,
            request.reference_scan_id,
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
