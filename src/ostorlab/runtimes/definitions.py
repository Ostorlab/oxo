"""Agent and Agent group definitions and settings dataclasses."""

import dataclasses
import io
import ipaddress
import json
import logging
import pathlib
from typing import Any, NamedTuple

from ostorlab.agent.schema import loader, validator
from ostorlab.assets import android_aab as android_aab_asset
from ostorlab.assets import android_apk as android_apk_asset
from ostorlab.assets import android_store as android_store_asset
from ostorlab.assets import api_schema as api_schema_asset
from ostorlab.assets import asset as base_asset
from ostorlab.assets import domain_name as domain_name_asset
from ostorlab.assets import file as file_asset
from ostorlab.assets import harmonyos_aab as harmonyos_aab_asset
from ostorlab.assets import harmonyos_apk as harmonyos_apk_asset
from ostorlab.assets import harmonyos_app as harmonyos_app_asset
from ostorlab.assets import harmonyos_hap as harmonyos_hap_asset
from ostorlab.assets import harmonyos_rpk as harmonyos_rpk_asset
from ostorlab.assets import harmonyos_store as harmonyos_store_asset
from ostorlab.assets import ios_ipa as ios_ipa_asset
from ostorlab.assets import ios_store as ios_store_asset
from ostorlab.assets import ipv4 as ipv4_asset
from ostorlab.assets import ipv6 as ipv6_asset
from ostorlab.assets import link as link_asset
from ostorlab.assets import multi_asset as multi_asset_asset
from ostorlab.assets import repository as repository_asset
from ostorlab.assets import repository_archive as repository_archive_asset
from ostorlab.assets import risk as risk_asset
from ostorlab.assets import ticket as ticket_asset
from ostorlab.cli import agent_fetcher
from ostorlab.runtimes.proto import agent_instance_settings_pb2
from ostorlab.utils import definitions

MAX_AGENT_REPLICAS = 100

_RISK_TARGET_KEYS = (
    "ip",
    "domain",
    "link",
    "androidStore",
    "iosStore",
    "androidApkFile",
    "androidAabFile",
    "iosFile",
    "repository",
    "repositoryArchive",
    "harmonyosStore",
    "harmonyosApkFile",
    "harmonyosAabFile",
    "harmonyosHapFile",
    "harmonyosAppFile",
    "harmonyosRpkFile",
)

_MULTI_ASSET_REPEATED_FIELDS: dict[type[base_asset.Asset], str] = {
    file_asset.File: "files",
    repository_asset.Repository: "repositories",
    repository_archive_asset.RepositoryArchive: "repository_archives",
    link_asset.Link: "urls",
    ipv4_asset.IPv4: "ipv4s",
    ipv6_asset.IPv6: "ipv6s",
    api_schema_asset.ApiSchema: "api_schemas",
}

_MULTI_ASSET_IP_KEYS = ("ip", "ipv4", "ipv6")

_MULTI_ASSET_REPEATED_FILE_CLASSES: dict[str, type[base_asset.Asset]] = {
    "file": file_asset.File,
    "repositoryArchive": repository_archive_asset.RepositoryArchive,
}

_MULTI_ASSET_MOBILE_FILE_CLASSES: dict[str, type[base_asset.Asset]] = {
    "androidApkFile": android_apk_asset.AndroidApk,
    "androidAabFile": android_aab_asset.AndroidAab,
    "iosFile": ios_ipa_asset.IOSIpa,
    "harmonyosHapFile": harmonyos_hap_asset.HarmonyOSHap,
    "harmonyosApkFile": harmonyos_apk_asset.HarmonyOSApk,
    "harmonyosAabFile": harmonyos_aab_asset.HarmonyOSAab,
    "harmonyosAppFile": harmonyos_app_asset.HarmonyOSApp,
    "harmonyosRpkFile": harmonyos_rpk_asset.HarmonyOSRpk,
}

_MULTI_ASSET_STORE_CLASSES: dict[str, tuple[type[base_asset.Asset], str]] = {
    "androidStore": (android_store_asset.AndroidStore, "package_name"),
    "iosStore": (ios_store_asset.IOSStore, "bundle_id"),
    "harmonyosStore": (harmonyos_store_asset.HarmonyOSStore, "bundle_name"),
}

_MULTI_ASSET_MOBILE_FIELDS: dict[type[base_asset.Asset], str] = {
    android_store_asset.AndroidStore: "android_package_name",
    ios_store_asset.IOSStore: "ios_bundle_id",
    harmonyos_store_asset.HarmonyOSStore: "harmonyos_bundle_name",
    android_apk_asset.AndroidApk: "android_apk",
    android_aab_asset.AndroidAab: "android_aab",
    ios_ipa_asset.IOSIpa: "ios_ipa",
    harmonyos_hap_asset.HarmonyOSHap: "harmonyos_hap",
    harmonyos_apk_asset.HarmonyOSApk: "harmonyos_apk",
    harmonyos_aab_asset.HarmonyOSAab: "harmonyos_aab",
    harmonyos_app_asset.HarmonyOSApp: "harmonyos_app",
    harmonyos_rpk_asset.HarmonyOSRpk: "harmonyos_rpk",
}

logger = logging.getLogger(__name__)


def _process_agent_replicas(replicas: int) -> int:
    """Add an upper & lower bounds to the number of replicas allowed for an Agent instance."""
    if replicas <= 0:
        return 1
    elif replicas > MAX_AGENT_REPLICAS:
        return MAX_AGENT_REPLICAS
    else:
        return replicas


@dataclasses.dataclass
class AgentSettings:
    """Agent instance lists the settings of running instance of an agent."""

    key: str
    version: str | None = None
    bus_url: str | None = ""
    bus_exchange_topic: str | None = ""
    bus_management_url: str | None = ""
    bus_vhost: str | None = ""
    args: list[definitions.Arg] = dataclasses.field(default_factory=list)
    constraints: list[str] | None = dataclasses.field(default_factory=list)
    mounts: list[str] | None = dataclasses.field(default_factory=list)
    restart_policy: str = ""
    mem_limit: int | None = None
    open_ports: list[definitions.PortMapping] = dataclasses.field(default_factory=list)
    replicas: int = 1
    healthcheck_host: str = "0.0.0.0"
    healthcheck_port: int = 5000
    redis_url: str | None = None
    tracing_collector_url: str | None = None
    caps: list[str] | None = None
    cyclic_processing_limit: int | None = None
    depth_processing_limit: int | None = None
    accepted_agents: list[str] | None = None
    in_selectors: list[str] | None = dataclasses.field(default_factory=list)
    service_name: str | None = None

    @property
    def container_image(self):
        return agent_fetcher.get_container_image(self.key, self.version)

    @classmethod
    def from_proto(cls, proto: bytes) -> "AgentSettings":
        """Constructs an agent definition from a binary proto settings.

        Args:
            proto: binary proto settings file.

        Returns:
            AgentInstanceSettings object.
        """
        instance = agent_instance_settings_pb2.AgentInstanceSettings()
        instance.ParseFromString(proto)
        return cls(
            key=instance.key,
            bus_url=instance.bus_url,
            bus_exchange_topic=instance.bus_exchange_topic,
            bus_management_url=instance.bus_management_url,
            bus_vhost=instance.bus_vhost,
            args=[
                definitions.Arg(name=a.name, type=a.type, value=a.value)
                for a in instance.args
            ],
            constraints=instance.constraints,
            mounts=instance.mounts,
            restart_policy=instance.restart_policy,
            mem_limit=instance.mem_limit,
            open_ports=[
                definitions.PortMapping(
                    source_port=p.source_port, destination_port=p.destination_port
                )
                for p in instance.open_ports
            ],
            replicas=instance.replicas,
            healthcheck_host=instance.healthcheck_host,
            healthcheck_port=instance.healthcheck_port,
            redis_url=instance.redis_url,
            tracing_collector_url=instance.tracing_collector_url,
            caps=instance.caps,
            cyclic_processing_limit=instance.cyclic_processing_limit,
            depth_processing_limit=instance.depth_processing_limit,
            accepted_agents=instance.accepted_agents,
            in_selectors=instance.in_selectors,
            service_name=instance.service_name or None,
        )

    def to_raw_proto(self) -> bytes:
        """Transforms agent instance settings into a raw proto bytes.

        Returns:
            Bytes as a serialized proto.
        """
        instance = agent_instance_settings_pb2.AgentInstanceSettings()
        instance.key = self.key
        instance.bus_url = self.bus_url
        instance.bus_exchange_topic = self.bus_exchange_topic
        instance.bus_management_url = self.bus_management_url
        instance.bus_vhost = self.bus_vhost

        for arg in self.args:
            arg_instance = instance.args.add()
            arg_instance.name = arg.name
            arg_instance.type = arg.type
            if isinstance(arg.value, bytes) and arg_instance.type != "binary":
                raise ValueError(
                    f"type {arg_instance.type} for not match value of type binary"
                )

            if isinstance(arg.value, bytes) and arg_instance.type == "binary":
                arg_instance.value = arg.value
            else:
                try:
                    arg_instance.value = json.dumps(arg.value).encode()
                except TypeError as e:
                    raise ValueError(
                        f"type {arg_instance.value} is not JSON serializable"
                    ) from e

        instance.constraints.extend(self.constraints)
        instance.mounts.extend(self.mounts)
        instance.restart_policy = self.restart_policy
        instance.in_selectors.extend(self.in_selectors)
        if self.mem_limit is not None:
            instance.mem_limit = self.mem_limit

        for open_port in self.open_ports:
            open_port_instance = instance.open_ports.add()
            open_port_instance.source_port = open_port.source_port
            open_port_instance.destination_port = open_port.destination_port

        instance.replicas = self.replicas
        instance.healthcheck_host = self.healthcheck_host
        instance.healthcheck_port = self.healthcheck_port
        if self.caps is not None:
            instance.caps.extend(self.caps)

        if self.cyclic_processing_limit is not None:
            instance.cyclic_processing_limit = self.cyclic_processing_limit

        if self.depth_processing_limit is not None:
            instance.depth_processing_limit = self.depth_processing_limit

        if self.accepted_agents is not None:
            instance.accepted_agents.extend(self.accepted_agents)

        if self.redis_url is not None:
            instance.redis_url = self.redis_url

        if self.tracing_collector_url is not None:
            instance.tracing_collector_url = self.tracing_collector_url

        if self.service_name is not None:
            instance.service_name = self.service_name

        return instance.SerializeToString()


@dataclasses.dataclass
class AgentGroupDefinition:
    """Data class holding the attributes of an agent."""

    agents: list[AgentSettings]
    name: str | None = None
    description: str | None = None
    use_experimental_agents: bool = False

    @classmethod
    def from_yaml(cls, group: io.FileIO):
        """Construct AgentGroupDefinition from yaml file.

        Args:
            group : agent group .yaml file.
        """
        agent_group_def = loader.load_agent_group_yaml(group)
        agent_settings = []
        agents_names = []
        for agent in agent_group_def["agents"]:
            agents_names.append(agent.get("key"))
            agent_def = AgentSettings(
                key=agent.get("key"),
                version=agent.get("version"),
                args=[
                    definitions.Arg(
                        name=a.get("name"),
                        description=a.get("description"),
                        type=a.get("type"),
                        value=a.get("value"),
                    )
                    for a in agent.get("args", [])
                ],
                constraints=agent.get("constraints", []),
                mounts=agent.get("mounts", []),
                restart_policy=agent.get("restart_policy", ""),
                mem_limit=agent.get("mem_limit"),
                open_ports=[
                    definitions.PortMapping(
                        source_port=p.get("src_port"),
                        destination_port=p.get("dest_port"),
                    )
                    for p in agent.get("open_ports", [])
                ],
                replicas=agent.get("replicas", 1),
                caps=agent.get("caps"),
                cyclic_processing_limit=agent.get("cyclic_processing_limit"),
                depth_processing_limit=agent.get("depth_processing_limit"),
                accepted_agents=agent.get("accepted_agents"),
                in_selectors=agent.get("in_selectors", []),
                service_name=agent.get("service_name"),
            )

            agent_settings.append(agent_def)

        name = agent_group_def.get("name")
        description = agent_group_def.get(
            "description", f"""Agent group : {",".join(agents_names)}"""
        )
        use_experimental_agents = agent_group_def.get("use_experimental_agents", False)
        return cls(agent_settings, name, description, use_experimental_agents)

    @classmethod
    def from_bus_message(cls, request):
        """Construct AgentGroupDefinition from a message received in the NATs.

        Args:
            request : The received message.
        """
        agent_settings = []
        agents_names = []
        for agent in request.agents:
            agents_names.append(agent.key)
            replicas = _process_agent_replicas(agent.replicas)
            agent_args = []
            for arg in agent.args:
                agent_arg = definitions.Arg.build(
                    name=arg.name,
                    type=arg.type,
                    value=arg.value,
                )
                agent_args.append(agent_arg)

            agent_def = AgentSettings(
                key=agent.key,
                version=agent.version,
                args=agent_args,
                replicas=replicas,
                caps=list(agent.caps),
                cyclic_processing_limit=agent.cyclic_processing_limit,
                depth_processing_limit=agent.depth_processing_limit,
                in_selectors=list(agent.in_selectors),
                open_ports=[
                    definitions.PortMapping(
                        source_port=p.src_port,
                        destination_port=p.dest_port,
                    )
                    for p in agent.open_ports
                ],
                service_name=agent.service_name or None,
            )

            agent_settings.append(agent_def)

        name = request.key.split("/")[-1]
        description = f"Agent group {name}: {','.join(agents_names)}"
        return cls(agent_settings, name, description)


@dataclasses.dataclass
class AssetsDefinition:
    targets: list[base_asset.Asset]
    name: str | None = None
    description: str | None = None

    @classmethod
    def from_yaml(cls, group: io.FileIO):
        """Construct TargetGroupDefinition from yaml file.

        Args:
            group : target group .yaml file.
        """
        target_group_def = loader.load_target_group_yaml(group)
        assets = target_group_def["assets"]
        android_store_assets = assets.get("androidStore", [])
        android_aab_file_assets = assets.get("androidAabFile", [])
        android_apk_file_assets = assets.get("androidApkFile", [])
        ios_store_assets = assets.get("iosStore", [])
        ios_file_assets = assets.get("iosFile", [])
        ip_assets = assets.get("ip", [])
        domain_assets = assets.get("domain", [])
        link_assets = assets.get("link", [])
        api_schema_assets = assets.get("apiSchema", [])
        ticket_assets = assets.get("ticket", [])
        risk_assets = assets.get("risk", [])
        repository_assets = assets.get("repository", [])
        repository_archive_assets = assets.get("repositoryArchive", [])

        assets_def: list[assets.Asset] = []

        for asset in android_aab_file_assets:
            parsed_file = _parse_file_asset(asset)
            if parsed_file is None:
                continue
            content, path, url = parsed_file
            assets_def.append(
                android_aab_asset.AndroidAab(
                    content=content, path=path, content_url=url
                )
            )

        for asset in android_apk_file_assets:
            parsed_file = _parse_file_asset(asset)
            if parsed_file is None:
                continue
            content, path, url = parsed_file
            assets_def.append(
                android_apk_asset.AndroidApk(
                    content=content, path=path, content_url=url
                )
            )

        for asset in ios_file_assets:
            parsed_file = _parse_file_asset(asset)
            if parsed_file is None:
                continue
            content, path, url = parsed_file
            assets_def.append(
                ios_ipa_asset.IOSIpa(content=content, path=path, content_url=url)
            )

        for asset in android_store_assets:
            assets_def.append(
                android_store_asset.AndroidStore(package_name=asset.get("package_name"))
            )

        for asset in ios_store_assets:
            assets_def.append(
                ios_store_asset.IOSStore(bundle_id=asset.get("bundle_id"))
            )

        for asset in ip_assets:
            ip_asset = _parse_ip_asset(asset)
            if ip_asset is not None:
                assets_def.append(ip_asset)

        for asset in domain_assets:
            assets_def.append(domain_name_asset.DomainName(name=asset.get("name")))

        for asset in link_assets:
            assets_def.append(
                link_asset.Link(url=asset.get("url"), method=asset.get("method"))
            )

        for asset in api_schema_assets:
            parsed_file = _parse_file_asset(asset)
            assets_def.append(
                api_schema_asset.ApiSchema(
                    endpoint_url=asset.get("endpoint_url"),
                    content=parsed_file.content if parsed_file is not None else None,
                    content_url=parsed_file.url if parsed_file is not None else None,
                    schema_type=asset.get("schema_type"),
                )
            )

        for asset in ticket_assets:
            parsed_comments = []
            for comment in asset.get("comments", []):
                parsed_comments.append(
                    ticket_asset.Comment(
                        author=comment.get("author"),
                        message=comment.get("message"),
                    )
                )
            assets_def.append(
                ticket_asset.Ticket(
                    title=asset.get("title"),
                    description=asset.get("description"),
                    ticket_id=asset.get("ticket_id"),
                    comments=parsed_comments,
                    ticket_key=asset.get("ticket_key"),
                )
            )

        for asset in repository_assets:
            repository_url = asset.get("repository_url")
            if repository_url is None or str(repository_url).strip() == "":
                raise validator.ValidationError(
                    "Repository requires a non-empty 'repository_url' field."
                )
            assets_def.append(_parse_repository_asset(asset))

        for asset in repository_archive_assets:
            parsed_file = _parse_file_asset(asset)
            if parsed_file is None:
                raise validator.ValidationError(
                    "Repository archive requires either a valid path or a content-url."
                )
            assets_def.append(
                repository_archive_asset.RepositoryArchive(
                    content=parsed_file.content,
                    path=parsed_file.path,
                    content_url=parsed_file.url,
                )
            )

        for asset in risk_assets:
            assets_def.append(_parse_risk_asset(asset))

        multi_asset_group = assets.get("multi_asset")
        if multi_asset_group is not None:
            bundled_asset = _parse_multi_asset(multi_asset_group)
            if bundled_asset is not None:
                assets_def.append(bundled_asset)

        return cls(
            targets=assets_def,
            name=target_group_def.get("name"),
            description=target_group_def.get("description"),
        )


def _bundle_multi_asset(
    targets: list[base_asset.Asset],
) -> multi_asset_asset.MultiAsset:
    """Group targets into a single multi asset.

    Raises ValidationError if a target has no matching field, or if more than one mobile
    asset is present."""
    multi_asset_kwargs: dict[str, Any] = {
        field: [] for field in _MULTI_ASSET_REPEATED_FIELDS.values()
    }
    unsupported_targets = []

    for target in targets:
        repeated_field = _MULTI_ASSET_REPEATED_FIELDS.get(type(target))
        if repeated_field is not None:
            multi_asset_kwargs[repeated_field].append(target)
            continue

        mobile_field = _MULTI_ASSET_MOBILE_FIELDS.get(type(target))
        if mobile_field is not None:
            multi_asset_kwargs[mobile_field] = target
            continue

        unsupported_targets.append(str(target))

    if len(unsupported_targets) > 0:
        raise validator.ValidationError(
            f"The multi asset message has no field for the following targets: "
            f"{', '.join(unsupported_targets)}."
        )

    bundled_asset = multi_asset_asset.MultiAsset(**multi_asset_kwargs)
    set_mobile_fields = bundled_asset.present_mobile_asset_fields
    if len(set_mobile_fields) > 1:
        # MultiAsset.to_proto enforces this same invariant with a ValueError; here at the
        # config-parsing layer we raise ValidationError so the CLI reports a config error.
        raise validator.ValidationError(
            multi_asset_asset.single_mobile_asset_error_message(set_mobile_fields)
        )
    return bundled_asset


def _parse_multi_asset(
    multi_asset_group: dict[str, Any],
) -> multi_asset_asset.MultiAsset | None:
    """Build a single multi asset from the target group's multi_asset section.

    Returns None when the section holds no asset, so no empty message is injected."""
    targets: list[base_asset.Asset] = []
    targets.extend(_parse_multi_asset_ips(multi_asset_group))
    targets.extend(_parse_multi_asset_links(multi_asset_group))
    targets.extend(_parse_multi_asset_repositories(multi_asset_group))
    targets.extend(_parse_multi_asset_api_schemas(multi_asset_group))
    targets.extend(_parse_multi_asset_files(multi_asset_group))
    targets.extend(_parse_multi_asset_stores(multi_asset_group))
    targets.extend(_parse_multi_asset_mobile_files(multi_asset_group))

    if len(targets) == 0:
        return None
    return _bundle_multi_asset(targets)


def _parse_multi_asset_ips(
    multi_asset_group: dict[str, Any],
) -> list[base_asset.Asset]:
    """Parse the ip, ipv4 and ipv6 entries, rejecting invalid IP addresses."""
    targets: list[base_asset.Asset] = []
    for yaml_key in _MULTI_ASSET_IP_KEYS:
        for entry in multi_asset_group.get(yaml_key, []):
            host = entry.get("host")
            if host is None or str(host).strip() == "":
                raise validator.ValidationError(
                    f"Multi asset {yaml_key} is missing required 'host' field."
                )
            ip = _parse_ip_asset(entry)
            if ip is None:
                raise validator.ValidationError(
                    f"Multi asset {yaml_key} has an invalid IP address: {host}."
                )
            if yaml_key == "ipv4" and isinstance(ip, ipv4_asset.IPv4) is False:
                raise validator.ValidationError(
                    f"Multi asset ipv4 entry has an IPv6 address: {host}."
                )
            if yaml_key == "ipv6" and isinstance(ip, ipv6_asset.IPv6) is False:
                raise validator.ValidationError(
                    f"Multi asset ipv6 entry has an IPv4 address: {host}."
                )
            targets.append(ip)
    return targets


def _parse_multi_asset_links(
    multi_asset_group: dict[str, Any],
) -> list[base_asset.Asset]:
    """Parse the link entries, rejecting entries with a missing or empty url."""
    targets: list[base_asset.Asset] = []
    for entry in multi_asset_group.get("link", []):
        url = entry.get("url")
        if url is None or str(url).strip() == "":
            raise validator.ValidationError(
                "Multi asset link requires a non-empty 'url' field."
            )
        targets.append(link_asset.Link(url=url, method=entry.get("method") or "GET"))
    return targets


def _parse_multi_asset_repositories(
    multi_asset_group: dict[str, Any],
) -> list[base_asset.Asset]:
    """Parse the repository entries, rejecting entries with an empty repository_url."""
    targets: list[base_asset.Asset] = []
    for entry in multi_asset_group.get("repository", []):
        repository_url = entry.get("repository_url")
        if repository_url is None or str(repository_url).strip() == "":
            raise validator.ValidationError(
                "Multi asset repository requires a non-empty 'repository_url' field."
            )
        targets.append(_parse_repository_asset(entry))
    return targets


def _parse_multi_asset_api_schemas(
    multi_asset_group: dict[str, Any],
) -> list[base_asset.Asset]:
    """Parse the apiSchema entries, requiring a non-empty endpoint_url."""
    targets: list[base_asset.Asset] = []
    for entry in multi_asset_group.get("apiSchema", []):
        endpoint_url = entry.get("endpoint_url")
        if endpoint_url is None or str(endpoint_url).strip() == "":
            raise validator.ValidationError(
                "Multi asset apiSchema requires a non-empty 'endpoint_url' field."
            )
        parsed_file = _parse_file_asset(entry)
        targets.append(
            api_schema_asset.ApiSchema(
                endpoint_url=endpoint_url,
                content=parsed_file.content if parsed_file is not None else None,
                content_url=parsed_file.url if parsed_file is not None else None,
                schema_type=entry.get("schema_type"),
            )
        )
    return targets


def _parse_multi_asset_files(
    multi_asset_group: dict[str, Any],
) -> list[base_asset.Asset]:
    """Parse the repeated file-backed entries (file, repositoryArchive)."""
    targets: list[base_asset.Asset] = []
    for yaml_key, asset_class in _MULTI_ASSET_REPEATED_FILE_CLASSES.items():
        for entry in multi_asset_group.get(yaml_key, []):
            targets.append(_build_multi_asset_file(entry, yaml_key, asset_class))
    return targets


def _parse_multi_asset_stores(
    multi_asset_group: dict[str, Any],
) -> list[base_asset.Asset]:
    """Parse the store entries, rejecting entries missing their identifier field."""
    targets: list[base_asset.Asset] = []
    for yaml_key, (asset_class, field) in _MULTI_ASSET_STORE_CLASSES.items():
        if multi_asset_group.get(yaml_key) is not None:
            field_value = multi_asset_group[yaml_key].get(field)
            if field_value is None or str(field_value).strip() == "":
                raise validator.ValidationError(
                    f"Multi asset {yaml_key} is missing required field '{field}'."
                )
            targets.append(asset_class(**{field: field_value}))
    return targets


def _parse_multi_asset_mobile_files(
    multi_asset_group: dict[str, Any],
) -> list[base_asset.Asset]:
    """Parse the single mobile file entries (apk, aab, ipa, harmonyos variants)."""
    targets: list[base_asset.Asset] = []
    for yaml_key, asset_class in _MULTI_ASSET_MOBILE_FILE_CLASSES.items():
        if multi_asset_group.get(yaml_key) is not None:
            targets.append(
                _build_multi_asset_file(
                    multi_asset_group[yaml_key], yaml_key, asset_class
                )
            )
    return targets


def _parse_repository_asset(entry: dict[str, Any]) -> repository_asset.Repository:
    """Build a repository asset, omitting an unset provider.

    Repository.__post_init__ drops an empty provider since the proto field is an enum
    with no empty member."""
    repository_url = str(entry.get("repository_url") or "")
    commit_hash = str(entry.get("commit_hash") or "")
    provider = entry.get("provider")
    if provider is None:
        return repository_asset.Repository(
            repository_url=repository_url, commit_hash=commit_hash
        )
    return repository_asset.Repository(
        repository_url=repository_url,
        commit_hash=commit_hash,
        provider=str(provider),
    )


def _build_multi_asset_file(
    entry: dict[str, Any], yaml_key: str, asset_class: type[base_asset.Asset]
) -> base_asset.Asset:
    """Build a file-backed multi asset target, rejecting entries with no path nor url."""
    parsed_file = _parse_file_asset(entry)
    if parsed_file is None:
        raise validator.ValidationError(
            f"Multi asset {yaml_key} requires either a valid path or a url."
        )
    built_asset: base_asset.Asset = asset_class(
        content=parsed_file.content,
        path=parsed_file.path,
        content_url=parsed_file.url,
    )
    return built_asset


class ParsedFileAsset(NamedTuple):
    """A file asset resolved into its content, local path and remote URL."""

    content: bytes | None
    path: str | None
    url: str | None


def _parse_file_asset(file_asset: dict[str, Any]) -> ParsedFileAsset | None:
    """Resolve a file asset entry into its content, path and url.

    Returns None when the entry has neither readable content nor a URL, so the
    caller can skip it (standalone assets) or reject it (embedded risk asset)."""
    # The iOS file schema historically spells the key ``paths``; accept both.
    path = file_asset.get("path") or file_asset.get("paths")
    url = file_asset.get("url")
    content = None
    if path is not None:
        content = _load_asset_from_file(path)
    if content is None and url is None:
        return None
    return ParsedFileAsset(content=content, path=path, url=url)


def _resolve_risk_file_asset(risk_entry: dict[str, Any], key: str) -> ParsedFileAsset:
    """Resolve a risk-embedded file asset, rejecting entries with no usable data."""
    parsed_file = _parse_file_asset(risk_entry[key])
    if parsed_file is None:
        raise validator.ValidationError(
            f"Risk {key} requires either a valid path or a url."
        )
    return parsed_file


def _resolve_risk_target_field(risk_entry: dict[str, Any], key: str, field: str) -> str:
    """Return a risk-embedded target's identifying field, rejecting empty entries.

    The target sub-schemas mark no field as required, so an entry like ``domain: {}``
    passes validation and would otherwise build a target with a ``None`` identifier
    that is silently dropped from the proto oneof."""
    value = risk_entry[key].get(field)
    if value is None or value == "":
        raise validator.ValidationError(f"Risk {key} requires a {field}.")
    return str(value)


def _parse_risk_asset(risk_entry: dict[str, Any]) -> risk_asset.Risk:
    """Build a Risk asset from a target group risk entry.

    The embedded target reuses the same sub-schemas as standalone assets
    (ip, domain, link, stores and app files). A risk carries a single target
    because the underlying proto asset is a oneof; embedding more than one
    would silently drop all but one."""
    provided_targets = [
        key for key in _RISK_TARGET_KEYS if risk_entry.get(key) is not None
    ]
    if len(provided_targets) > 1:
        raise validator.ValidationError(
            f"A risk asset must embed at most one target, got: {', '.join(provided_targets)}."
        )

    risk_kwargs: dict[str, Any] = {
        "description": risk_entry["description"],
        "rating": risk_entry["severity"],
    }

    if risk_entry.get("ip") is not None:
        ip_asset = _parse_ip_asset(risk_entry["ip"])
        if isinstance(ip_asset, ipv4_asset.IPv4):
            risk_kwargs["ipv4"] = ip_asset
        elif isinstance(ip_asset, ipv6_asset.IPv6):
            risk_kwargs["ipv6"] = ip_asset
        else:
            raise validator.ValidationError(
                f"Risk asset has an invalid IP address: {risk_entry['ip'].get('host')}"
            )

    if risk_entry.get("domain") is not None:
        risk_kwargs["domain_name"] = domain_name_asset.DomainName(
            name=_resolve_risk_target_field(risk_entry, "domain", "name")
        )

    if risk_entry.get("link") is not None:
        risk_kwargs["link"] = link_asset.Link(
            url=_resolve_risk_target_field(risk_entry, "link", "url"),
            method=risk_entry["link"].get("method") or "GET",
        )

    if risk_entry.get("androidStore") is not None:
        risk_kwargs["android_store"] = android_store_asset.AndroidStore(
            package_name=_resolve_risk_target_field(
                risk_entry, "androidStore", "package_name"
            )
        )

    if risk_entry.get("iosStore") is not None:
        risk_kwargs["ios_store"] = ios_store_asset.IOSStore(
            bundle_id=_resolve_risk_target_field(risk_entry, "iosStore", "bundle_id")
        )

    if risk_entry.get("androidApkFile") is not None:
        content, path, url = _resolve_risk_file_asset(risk_entry, "androidApkFile")
        risk_kwargs["android_apk"] = android_apk_asset.AndroidApk(
            content=content, path=path, content_url=url
        )

    if risk_entry.get("androidAabFile") is not None:
        content, path, url = _resolve_risk_file_asset(risk_entry, "androidAabFile")
        risk_kwargs["android_aab"] = android_aab_asset.AndroidAab(
            content=content, path=path, content_url=url
        )

    if risk_entry.get("iosFile") is not None:
        content, path, url = _resolve_risk_file_asset(risk_entry, "iosFile")
        risk_kwargs["ios_ipa"] = ios_ipa_asset.IOSIpa(
            content=content, path=path, content_url=url
        )

    if risk_entry.get("repository") is not None:
        risk_kwargs["repository"] = repository_asset.Repository(
            repository_url=_resolve_risk_target_field(
                risk_entry, "repository", "repository_url"
            ),
            commit_hash=risk_entry["repository"].get("commit_hash") or "",
        )

    if risk_entry.get("repositoryArchive") is not None:
        content, path, url = _resolve_risk_file_asset(risk_entry, "repositoryArchive")
        risk_kwargs["repository_archive"] = repository_archive_asset.RepositoryArchive(
            content=content, path=path, content_url=url
        )

    if risk_entry.get("harmonyosStore") is not None:
        risk_kwargs["harmonyos_store"] = harmonyos_store_asset.HarmonyOSStore(
            bundle_name=_resolve_risk_target_field(
                risk_entry, "harmonyosStore", "bundle_name"
            )
        )

    if risk_entry.get("harmonyosApkFile") is not None:
        content, path, url = _resolve_risk_file_asset(risk_entry, "harmonyosApkFile")
        risk_kwargs["harmonyos_apk"] = harmonyos_apk_asset.HarmonyOSApk(
            content=content, path=path, content_url=url
        )

    if risk_entry.get("harmonyosAabFile") is not None:
        content, path, url = _resolve_risk_file_asset(risk_entry, "harmonyosAabFile")
        risk_kwargs["harmonyos_aab"] = harmonyos_aab_asset.HarmonyOSAab(
            content=content, path=path, content_url=url
        )

    if risk_entry.get("harmonyosHapFile") is not None:
        content, path, url = _resolve_risk_file_asset(risk_entry, "harmonyosHapFile")
        risk_kwargs["harmonyos_hap"] = harmonyos_hap_asset.HarmonyOSHap(
            content=content, path=path, content_url=url
        )

    if risk_entry.get("harmonyosAppFile") is not None:
        content, path, url = _resolve_risk_file_asset(risk_entry, "harmonyosAppFile")
        risk_kwargs["harmonyos_app"] = harmonyos_app_asset.HarmonyOSApp(
            content=content, path=path, content_url=url
        )

    if risk_entry.get("harmonyosRpkFile") is not None:
        content, path, url = _resolve_risk_file_asset(risk_entry, "harmonyosRpkFile")
        risk_kwargs["harmonyos_rpk"] = harmonyos_rpk_asset.HarmonyOSRpk(
            content=content, path=path, content_url=url
        )

    return risk_asset.Risk(**risk_kwargs)


def _parse_ip_asset(ip_asset: dict[str, Any]) -> base_asset.Asset | None:
    ip_string = ip_asset.get("host")
    try:
        ip = ipaddress.ip_address(ip_string)
    except ValueError:
        logger.info(f"Invalid ip address: {ip_string}")
        return None

    mask = ip_asset.get("mask")
    mask = str(mask) if mask is not None else None
    if ip.version == 4:
        return ipv4_asset.IPv4(host=ip_string, mask=mask)
    if ip.version == 6:
        return ipv6_asset.IPv6(host=ip_string, mask=mask)
    return None


def _load_asset_from_file(path: str) -> bytes | None:
    path = pathlib.Path(path)
    try:
        content = path.read_bytes()
    except OSError as e:
        logger.error(f"Could not open {path}: {e}.")
        return None
    return content
