"""Risk message asset for injecting risk reports onto the message bus."""

import dataclasses
from typing import Any
from typing import Optional

from ostorlab.agent.message import serializer
from ostorlab.assets import android_aab as android_aab_asset
from ostorlab.assets import android_apk as android_apk_asset
from ostorlab.assets import android_store as android_store_asset
from ostorlab.assets import api_schema as api_schema_asset
from ostorlab.assets import asset
from ostorlab.assets import domain_name as domain_name_asset
from ostorlab.assets import harmonyos_aab as harmonyos_aab_asset
from ostorlab.assets import harmonyos_apk as harmonyos_apk_asset
from ostorlab.assets import harmonyos_app as harmonyos_app_asset
from ostorlab.assets import harmonyos_hap as harmonyos_hap_asset
from ostorlab.assets import harmonyos_rpk as harmonyos_rpk_asset
from ostorlab.assets import harmonyos_store as harmonyos_store_asset
from ostorlab.assets import ios_ipa as ios_ipa_asset
from ostorlab.assets import ios_store as ios_store_asset
from ostorlab.assets import ios_testflight as ios_testflight_asset
from ostorlab.assets import ipv4 as ipv4_asset
from ostorlab.assets import ipv6 as ipv6_asset
from ostorlab.assets import link as link_asset
from ostorlab.assets import multi_asset as multi_asset_asset
from ostorlab.assets import repository as repository_asset
from ostorlab.assets import repository_archive as repository_archive_asset


@dataclasses.dataclass
@asset.selector("v3.report.risk")
class Risk(asset.Asset):
    """Risk report to be injected onto the message bus."""

    description: str
    rating: str
    domain_name: Optional[domain_name_asset.DomainName | dict[str, Any]] = None
    ipv4: Optional[ipv4_asset.IPv4 | dict[str, Any]] = None
    ipv6: Optional[ipv6_asset.IPv6 | dict[str, Any]] = None
    link: Optional[link_asset.Link | dict[str, Any]] = None
    android_store: Optional[android_store_asset.AndroidStore | dict[str, Any]] = None
    ios_store: Optional[ios_store_asset.IOSStore | dict[str, Any]] = None
    ios_testflight: Optional[ios_testflight_asset.IOSTestflight | dict[str, Any]] = None
    android_aab: Optional[android_aab_asset.AndroidAab | dict[str, Any]] = None
    android_apk: Optional[android_apk_asset.AndroidApk | dict[str, Any]] = None
    ios_ipa: Optional[ios_ipa_asset.IOSIpa | dict[str, Any]] = None
    api_schema: Optional[api_schema_asset.ApiSchema | dict[str, Any]] = None
    repository: Optional[repository_asset.Repository | dict[str, Any]] = None
    repository_archive: Optional[
        repository_archive_asset.RepositoryArchive | dict[str, Any]
    ] = None
    harmonyos_store: Optional[harmonyos_store_asset.HarmonyOSStore | dict[str, Any]] = (
        None
    )
    harmonyos_apk: Optional[harmonyos_apk_asset.HarmonyOSApk | dict[str, Any]] = None
    harmonyos_aab: Optional[harmonyos_aab_asset.HarmonyOSAab | dict[str, Any]] = None
    harmonyos_hap: Optional[harmonyos_hap_asset.HarmonyOSHap | dict[str, Any]] = None
    harmonyos_app: Optional[harmonyos_app_asset.HarmonyOSApp | dict[str, Any]] = None
    harmonyos_rpk: Optional[harmonyos_rpk_asset.HarmonyOSRpk | dict[str, Any]] = None
    multi_asset: Optional[multi_asset_asset.MultiAsset | dict[str, Any]] = None

    def to_proto(self) -> bytes:
        data = {
            k: (v.__dict__ if isinstance(v, asset.Asset) else v)
            for k, v in self.__dict__.items()
        }
        return bytes(serializer.serialize(self.selector, data).SerializeToString())

    @property
    def proto_field(self) -> str:
        return "risk"

    def __str__(self) -> str:
        return f"Risk({self.rating}: {self.description})"
