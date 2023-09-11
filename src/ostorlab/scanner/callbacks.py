"""Defines call back to trigger a scan after receiving a startAgentScan messages in the NATS."""
import logging
import ipaddress
from typing import List, Any, Optional

import docker

from ostorlab.runtimes import registry
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime
from ostorlab.cli import install_agent
from ostorlab.assets import asset
from ostorlab.assets import ipv4
from ostorlab.assets import ipv6
from ostorlab.assets import android_store
from ostorlab.assets import android_aab
from ostorlab.assets import android_apk
from ostorlab.assets import file
from ostorlab.assets import ios_ipa
from ostorlab.assets import domain_name
from ostorlab.assets import link as link_asset
from ostorlab.assets import ios_store
from ostorlab.assets import agent as agent_asset
from ostorlab.utils import scanner_state_reporter
from ostorlab.scanner import scanner_conf


logger = logging.getLogger(__name__)


def _install_agents(
    runtime_instance: runtime.Runtime,
    agents,
    docker_client: Optional[docker.DockerClient] = None,
) -> None:
    """Trigger installation of the agents that will run the scan."""
    try:
        runtime_instance.install(docker_client=docker_client)
        for agent in agents:
            install_agent.install(
                agent_key=agent.key, version=agent.version, docker_client=docker_client
            )
    except install_agent.AgentDetailsNotFound:
        logger.warning("agent %s not found on the store", agent.key)


def _prepare_ip_asset(ip_request) -> asset.Asset:
    """Return IP assets from a NATs received message."""
    ip_network = ipaddress.ip_network(ip_request.host, strict=False)
    if ip_network.version == 4:
        return ipv4.IPv4(
            host=ip_network.network_address.exploded,
            mask=ip_request.mask or str(ip_network.prefixlen),
        )
    elif ip_network.version == 6:
        return ipv6.IPv6(
            host=ip_network.network_address.exploded,
            mask=ip_request.mask or str(ip_network.prefixlen),
        )
    else:
        raise ValueError(f"Invalid Ip address {ip_request.host}")


def _extract_assets(request: Any) -> List[asset.Asset]:
    """Returns list of specific Ostorlab-injectable assets, from a message received from NATs."""
    logger.debug("Extracting assets.")
    assets = []
    asset_type = request.WhichOneof("asset")
    if asset_type in ("ip", "ip4v", "ipv6"):
        ip_request = request.ip or request.ipv4 or request.ipv6
        assets.append(_prepare_ip_asset(ip_request))

    elif asset_type == "android_store":
        assets.append(
            android_store.AndroidStore(package_name=request.android_store.package_name)
        )

    elif asset_type == "ios_store":
        assets.append(ios_store.IOSStore(bundle_id=request.ios_store.bundle_id))

    elif asset_type == "ipa":
        assets.append(
            ios_ipa.IOSIpa(
                content=request.ipa.content,
                path=request.ipa.path,
                content_url=request.ipa.content_url,
            )
        )
    elif asset_type == "apk":
        assets.append(
            android_apk.AndroidApk(
                content=request.apk.content,
                path=request.apk.path,
                content_url=request.apk.content_url,
            )
        )
    elif asset_type == "aab":
        assets.append(
            android_aab.AndroidAab(
                content=request.aab.content,
                path=request.aab.path,
                content_url=request.aab.content_url,
            )
        )
    elif asset_type == "domain":
        assets.append(domain_name.DomainName(name=request.domain_name.name))

    elif asset_type == "agent":
        assets.append(
            agent_asset.Agent(
                key=request.agent.key,
                version=request.agent.version,
                git_location=request.agent.git_location,
                docker_location=request.agent.docker_location,
                yaml_file_location=request.agent.yaml_file_location,
            )
        )

    elif asset_type == "file":
        assets.append(
            file.File(
                content=request.file.content,
                path=request.file.path,
                content_url=request.file.content_url,
            )
        )
    elif asset_type == "network":
        for ip in request.network.ips:
            ip_asset = _prepare_ip_asset(ip)
            assets.append(ip_asset)

    elif asset_type == "links":
        for link in request.links.links:
            assets.append(
                link_asset.Link(
                    url=link.url,
                    method=link.url or "GET",
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


def _connect_containers_registry(
    configuration: scanner_conf.RegistryConfig,
) -> docker.DockerClient:
    """Connect to container registry."""
    logger.debug("Connecting to private container registry.")
    client = docker.from_env()
    client.login(
        username=configuration.username,
        password=configuration.token,
        registry=configuration.url,
    )
    return client


def start_scan(
    subject: str,
    request: Any,
    state_reporter: scanner_state_reporter.ScannerStateReporter,
    registry_conf: scanner_conf.RegistryConfig,
) -> str:
    """Responsible for triggering an Ostorlab scan, after receiving a startAgentScan message in NATs.

    Args:
        subject: Subject of the received message.
        request: Deserialized message.
        state_reporter: State reporter instance responsible for sending current state of the scanner.
        registry_conf: Credentials to the registry, useful to pull agents images.
    """
    logger.debug("Triggering scan after receiving message on: %s", subject)
    docker_client = _connect_containers_registry(configuration=registry_conf)

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
        )

        runtime_instance.scan(
            agent_group_definition=agent_group_definition,
            assets=assets,
            title=None,
        )
        return runtime_instance.name
    else:
        logger.error(
            "The runtime does not support the provided agent list or group definition."
        )
