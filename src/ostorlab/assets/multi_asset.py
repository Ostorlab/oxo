"""Multi asset."""

import dataclasses
from typing import Any

from ostorlab.agent.message import serializer
from ostorlab.assets import android_aab as android_aab_asset
from ostorlab.assets import android_apk as android_apk_asset
from ostorlab.assets import android_store as android_store_asset
from ostorlab.assets import api_schema as api_schema_asset
from ostorlab.assets import asset
from ostorlab.assets import file as file_asset
from ostorlab.assets import harmonyos_aab as harmonyos_aab_asset
from ostorlab.assets import harmonyos_apk as harmonyos_apk_asset
from ostorlab.assets import harmonyos_app as harmonyos_app_asset
from ostorlab.assets import harmonyos_hap as harmonyos_hap_asset
from ostorlab.assets import harmonyos_rpk as harmonyos_rpk_asset
from ostorlab.assets import harmonyos_store as harmonyos_store_asset
from ostorlab.assets import ios_ipa as ios_ipa_asset
from ostorlab.assets import ios_store as ios_store_asset
from ostorlab.assets import ip as ip_asset
from ostorlab.assets import ipv4 as ipv4_asset
from ostorlab.assets import ipv6 as ipv6_asset
from ostorlab.assets import link as link_asset
from ostorlab.assets import repository as repository_asset
from ostorlab.assets import repository_archive as repository_archive_asset


MOBILE_ASSET_FIELDS: frozenset[str] = frozenset(
    {
        "android_package_name",
        "ios_bundle_id",
        "harmonyos_bundle_name",
        "android_apk",
        "android_aab",
        "ios_ipa",
        "harmonyos_hap",
        "harmonyos_apk",
        "harmonyos_aab",
        "harmonyos_app",
        "harmonyos_rpk",
    }
)


def _asset_fields(nested_asset: asset.Asset) -> dict[str, Any]:
    """Map a nested asset to its set dataclass fields, dropping unset optionals
    and attributes removed in __post_init__ (e.g. Repository.provider)."""
    instance_values = nested_asset.__dict__
    declared_fields = dataclasses.fields(nested_asset)  # type: ignore[arg-type]
    return {
        field.name: instance_values[field.name]
        for field in declared_fields
        if field.name in instance_values and instance_values[field.name] is not None
    }


def single_mobile_asset_error_message(mobile_fields: list[str]) -> str:
    """Build the error message shown when more than one mobile asset is bundled."""
    return (
        f"A multi asset accepts at most one mobile asset, got: "
        f"{', '.join(mobile_fields)}."
    )


@dataclasses.dataclass
@asset.selector("v3.asset.multi_asset")
class MultiAsset(asset.Asset):
    """Multi-asset target grouping heterogeneous assets in a single scan target."""

    files: list[file_asset.File] = dataclasses.field(default_factory=list)
    android_package_name: android_store_asset.AndroidStore | None = None
    ios_bundle_id: ios_store_asset.IOSStore | None = None
    harmonyos_bundle_name: harmonyos_store_asset.HarmonyOSStore | None = None
    android_apk: android_apk_asset.AndroidApk | None = None
    android_aab: android_aab_asset.AndroidAab | None = None
    ios_ipa: ios_ipa_asset.IOSIpa | None = None
    harmonyos_hap: harmonyos_hap_asset.HarmonyOSHap | None = None
    harmonyos_apk: harmonyos_apk_asset.HarmonyOSApk | None = None
    harmonyos_aab: harmonyos_aab_asset.HarmonyOSAab | None = None
    harmonyos_app: harmonyos_app_asset.HarmonyOSApp | None = None
    harmonyos_rpk: harmonyos_rpk_asset.HarmonyOSRpk | None = None
    repositories: list[repository_asset.Repository] = dataclasses.field(
        default_factory=list
    )
    repository_archives: list[repository_archive_asset.RepositoryArchive] = (
        dataclasses.field(default_factory=list)
    )
    urls: list[link_asset.Link] = dataclasses.field(default_factory=list)
    ips: list[ip_asset.IP] = dataclasses.field(default_factory=list)
    ipv4s: list[ipv4_asset.IPv4] = dataclasses.field(default_factory=list)
    ipv6s: list[ipv6_asset.IPv6] = dataclasses.field(default_factory=list)
    api_schemas: list[api_schema_asset.ApiSchema] = dataclasses.field(
        default_factory=list
    )

    def __str__(self) -> str:
        nested_assets = [
            str(nested_asset)
            for nested_asset in self.nested_assets()
            if nested_asset is not None
        ]
        return f"MultiAsset: [{', '.join(nested_assets)}]"

    def nested_assets(self) -> list[asset.Asset | None]:
        return [
            *self.files,
            self.android_package_name,
            self.ios_bundle_id,
            self.harmonyos_bundle_name,
            self.android_apk,
            self.android_aab,
            self.ios_ipa,
            self.harmonyos_hap,
            self.harmonyos_apk,
            self.harmonyos_aab,
            self.harmonyos_app,
            self.harmonyos_rpk,
            *self.repositories,
            *self.repository_archives,
            *self.urls,
            *self.ips,
            *self.ipv4s,
            *self.ipv6s,
            *self.api_schemas,
        ]

    @property
    def present_mobile_asset_fields(self) -> list[str]:
        """Names of the mobile asset fields that are set."""
        return [
            key
            for key, value in self.__dict__.items()
            if key in MOBILE_ASSET_FIELDS and value is not None
        ]

    def to_proto(self) -> bytes:
        """Serialize the grouped assets into a single multi asset proto message.

        Raises ValueError if more than one mobile asset is set, since the proto oneof
        would silently drop the extras."""
        set_mobile_fields = self.present_mobile_asset_fields
        if len(set_mobile_fields) > 1:
            raise ValueError(single_mobile_asset_error_message(set_mobile_fields))

        data: dict[str, Any] = {}
        for key, value in self.__dict__.items():
            if value is None:
                continue
            if isinstance(value, asset.Asset):
                data[key] = _asset_fields(value)
            elif isinstance(value, list):
                data[key] = [
                    _asset_fields(entry) if isinstance(entry, asset.Asset) else entry
                    for entry in value
                ]
            else:
                data[key] = value

        return bytes(serializer.serialize(self.selector, data).SerializeToString())

    @property
    def proto_field(self) -> str:
        return "multi_asset"
