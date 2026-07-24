"""Risk message asset for injecting risk reports onto the message bus."""

import dataclasses

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
    domain_name: domain_name_asset.DomainName | None = None
    ipv4: ipv4_asset.IPv4 | None = None
    ipv6: ipv6_asset.IPv6 | None = None
    link: link_asset.Link | None = None
    android_store: android_store_asset.AndroidStore | None = None
    ios_store: ios_store_asset.IOSStore | None = None
    android_aab: android_aab_asset.AndroidAab | None = None
    android_apk: android_apk_asset.AndroidApk | None = None
    ios_ipa: ios_ipa_asset.IOSIpa | None = None
    api_schema: api_schema_asset.ApiSchema | None = None
    repository: repository_asset.Repository | None = None
    repository_archive: repository_archive_asset.RepositoryArchive | None = None
    harmonyos_store: harmonyos_store_asset.HarmonyOSStore | None = None
    harmonyos_apk: harmonyos_apk_asset.HarmonyOSApk | None = None
    harmonyos_aab: harmonyos_aab_asset.HarmonyOSAab | None = None
    harmonyos_hap: harmonyos_hap_asset.HarmonyOSHap | None = None
    harmonyos_app: harmonyos_app_asset.HarmonyOSApp | None = None
    harmonyos_rpk: harmonyos_rpk_asset.HarmonyOSRpk | None = None
    multi_asset: multi_asset_asset.MultiAsset | None = None

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
