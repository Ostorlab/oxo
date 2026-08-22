"""Defines call back to trigger a scan after receiving a startAgentScan messages in the NATS."""

from __future__ import annotations

import base64
import binascii
import contextlib
import ipaddress
import logging
from typing import Any

import docker


from ostorlab import exceptions
from ostorlab.assets import agent as agent_asset
from ostorlab.assets import (
    android_aab,
    android_apk,
    android_store,
    api_schema,
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
    ios_testflight,
    ipv4,
    ipv6,
)
from ostorlab.assets import link as link_asset
from ostorlab.assets import repository as repository_asset
from ostorlab.assets import repository_archive as repository_archive_asset
from ostorlab.assets import risk as risk_asset
from ostorlab.assets import ticket as ticket_asset
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


def _prepare_network_asset(netwrok_asset_value: str) -> asset.Asset:
    """Return IP assets from network_asset_value str."""
    ip_network = ipaddress.ip_network(netwrok_asset_value, strict=False)
    if ip_network.version == 4:
        return ipv4.IPv4(
            host=ip_network.network_address.exploded,
            mask=str(ip_network.prefixlen),
        )
    elif ip_network.version == 6:
        return ipv6.IPv6(
            host=ip_network.network_address.exploded,
            mask=str(ip_network.prefixlen),
        )
    else:
        raise ValueError(f"Invalid Network address {netwrok_asset_value}")


def _build_risk_kwargs(target_dict: dict[str, Any] | None) -> dict[str, Any]:
    """Builds risk kwargs for the first resolved target asset."""
    if target_dict is None:
        return {}

    target_assets = _extract_assets(target_dict)
    if len(target_assets) > 1:
        logger.warning(
            "Risk target has multiple assets, Risk will only associate with the first asset."
        )

    if len(target_assets) == 0:
        return {}

    target_asset = target_assets[0]
    kwargs = {}
    if isinstance(target_asset, ipv4.IPv4):
        kwargs["ipv4"] = target_asset
    elif isinstance(target_asset, ipv6.IPv6):
        kwargs["ipv6"] = target_asset
    elif isinstance(target_asset, link_asset.Link):
        kwargs["link"] = target_asset
    elif isinstance(target_asset, domain_name.DomainName):
        kwargs["domain_name"] = target_asset
    elif isinstance(target_asset, android_store.AndroidStore):
        kwargs["android_store"] = target_asset
    elif isinstance(target_asset, ios_store.IOSStore):
        kwargs["ios_store"] = target_asset
    elif isinstance(target_asset, android_aab.AndroidAab):
        kwargs["android_aab"] = target_asset
    elif isinstance(target_asset, android_apk.AndroidApk):
        kwargs["android_apk"] = target_asset
    elif isinstance(target_asset, ios_ipa.IOSIpa):
        kwargs["ios_ipa"] = target_asset
    elif isinstance(target_asset, repository_asset.Repository):
        kwargs["repository"] = target_asset
    elif isinstance(target_asset, repository_archive_asset.RepositoryArchive):
        kwargs["repository_archive"] = target_asset
    elif isinstance(target_asset, ios_testflight.IOSTestflight):
        kwargs["ios_testflight"] = target_asset
    elif isinstance(target_asset, file.File):
        kwargs["file"] = target_asset
    elif isinstance(target_asset, api_schema.ApiSchema):
        kwargs["api_schema"] = target_asset
    elif isinstance(target_asset, harmonyos_store.HarmonyOSStore):
        kwargs["harmonyos_store"] = target_asset
    elif isinstance(target_asset, harmonyos_apk.HarmonyOSApk):
        kwargs["harmonyos_apk"] = target_asset
    elif isinstance(target_asset, harmonyos_aab.HarmonyOSAab):
        kwargs["harmonyos_aab"] = target_asset
    elif isinstance(target_asset, harmonyos_hap.HarmonyOSHap):
        kwargs["harmonyos_hap"] = target_asset
    elif isinstance(target_asset, harmonyos_app.HarmonyOSApp):
        kwargs["harmonyos_app"] = target_asset
    elif isinstance(target_asset, harmonyos_rpk.HarmonyOSRpk):
        kwargs["harmonyos_rpk"] = target_asset
    else:
        logger.warning(
            "Risk target asset %s is not fully mapped in Risk.",
            type(target_asset).__name__,
        )
    return kwargs


def _extract_assets(asset_data: dict[str, Any]) -> list[asset.Asset]:
    """Directly parses a GraphQL asset dictionary into Ostorlab Asset objects."""
    if asset_data is None or asset_data == {}:
        return []

    typename = asset_data.get("__typename")

    kwargs = {k: v for k, v in asset_data.items() if k != "__typename"}

    if "content" in kwargs and isinstance(kwargs["content"], str):
        try:
            kwargs["content"] = base64.b64decode(kwargs["content"], validate=True)
        except binascii.Error:
            kwargs["content"] = kwargs["content"].encode()

    if typename in ("Ipv4AssetType", "Ipv6AssetType", "IpAssetType"):
        return [_prepare_ip_asset(ip_asset_value=kwargs)]
    elif typename == "NetworkAssetType":
        return [
            _prepare_network_asset(netwrok_asset_value=network)
            for network in kwargs.get("networks") or []
        ]
    elif typename == "UrlAssetType":
        return [
            link_asset.Link(url=link, method="GET") for link in kwargs.get("urls") or []
        ]
    elif typename == "AndroidPackageNameAssetType":
        return [android_store.AndroidStore(package_name=kwargs.get("packageName", ""))]
    elif typename == "IosBundleIdAssetType":
        return [ios_store.IOSStore(bundle_id=kwargs.get("bundleId", ""))]
    elif typename == "IosTestflightAssetType":
        return [
            ios_testflight.IOSTestflight(
                application_url=kwargs.get("applicationUrl", "")
            )
        ]
    elif typename == "ApiSchemaAssetType":
        return [
            api_schema.ApiSchema(
                endpoint_url=kwargs.get("endpointUrl", ""),
                content=kwargs.get("content"),
                path=kwargs.get("path"),
                content_url=kwargs.get("contentUrl"),
                schema_type=kwargs.get("schemaType"),
            )
        ]
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
        return [
            harmonyos_store.HarmonyOSStore(bundle_name=kwargs.get("bundleName") or "")
        ]
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
    elif typename == "TicketAssetType":
        parsed_comments = []
        for comment in kwargs.get("ticketComments") or []:
            parsed_comments.append(
                ticket_asset.Comment(
                    author=comment.get("author"),
                    message=comment.get("value"),
                )
            )
        return [
            ticket_asset.Ticket(
                title=kwargs.get("title", ""),
                description=kwargs.get("description", ""),
                ticket_id=kwargs.get("ticketId"),
                ticket_key=kwargs.get("ticketKey"),
                comments=parsed_comments,
            )
        ]
    elif typename == "RiskAssetType":
        return [
            risk_asset.Risk(
                description=kwargs.get("description", ""),
                rating=kwargs.get("rating", ""),
                **_build_risk_kwargs(kwargs.get("target")),
            )
        ]
    elif typename == "RisksAssetType":
        return [
            risk_asset.Risk(
                description=risk_item.get("description", ""),
                rating=risk_item.get("rating", ""),
                **_build_risk_kwargs(risk_item.get("target")),
            )
            for risk_item in (kwargs.get("risks") or [])
        ]

    else:
        logger.error("%s not supported from scan asset payload", typename)
        return []


def _extract_agent_group_definition(
    request: dict[str, Any],
) -> definitions.AgentGroupDefinition:
    agent_group_definition = definitions.AgentGroupDefinition.from_api_response(request)
    logger.debug("Extracted agent group definition: %s.", agent_group_definition)
    return agent_group_definition


def _extract_scan_id(request: dict[str, Any]) -> int:
    scan_id = int(request.get("id"))
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
    request: dict[str, Any],
    state_reporter: scanner_state_reporter.ScannerStateReporter,
    api_key: str | None = None,
    gcp_logging_credential: str | None = None,
) -> str | None:
    """Responsible for triggering an Ostorlab scan, after receiving a scan from the API.

    Args:
        request: API response data for the scan.
        state_reporter: State reporter instance responsible for sending current state of the scanner.
        api_key: Optional api key to fetch short-lived download tokens for agent images.
        gcp_logging_credential: GCP Logging JSON credentials for agent containers.
    """
    logger.debug("Triggering scan after receiving scan from API")
    with contextlib.closing(_connect_containers_registry()) as docker_client:
        agent_group_data = request.get("agentGroup") or {}
        agent_group_definition = _extract_agent_group_definition(
            request=agent_group_data
        )
        assets = _extract_assets(asset_data=request.get("asset"))
        scan_id = _extract_scan_id(request=request)

        state_reporter = _update_state_reporter(
            state_reporter=state_reporter, scan_id=scan_id
        )

        runtime_instance = registry.select_runtime(
            runtime_type="local",
            scan_id=str(scan_id),
            run_default_agents=False,
            gcp_logging_credential=gcp_logging_credential,
        )

        if (
            runtime_instance.can_run(agent_group_definition=agent_group_definition)
            is True
        ):
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
                logger.error("An error was encountered while running the scan: %s", e)
                raise

            return runtime_instance.name
        else:
            logger.error(
                "The runtime does not support the provided agent list or group definition."
            )
