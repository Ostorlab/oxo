"""Risk message asset for injecting risk reports onto the message bus."""

import dataclasses
from typing import Optional

from ostorlab.assets import android_aab as android_aab_asset
from ostorlab.assets import android_apk as android_apk_asset
from ostorlab.assets import android_store as android_store_asset
from ostorlab.assets import api_schema as api_schema_asset
from ostorlab.agent.message import serializer
from ostorlab.assets import asset
from ostorlab.assets import domain_name as domain_name_asset
from ostorlab.assets import ios_ipa as ios_ipa_asset
from ostorlab.assets import ios_store as ios_store_asset
from ostorlab.assets import ipv4 as ipv4_asset
from ostorlab.assets import ipv6 as ipv6_asset
from ostorlab.assets import link as link_asset


@dataclasses.dataclass
@asset.selector("v3.report.risk")
class Risk(asset.Asset):
    """Risk report to be injected onto the message bus."""

    description: str
    rating: str
    domain_name: Optional[domain_name_asset.DomainName] = None
    ipv4: Optional[ipv4_asset.IPv4] = None
    ipv6: Optional[ipv6_asset.IPv6] = None
    link: Optional[link_asset.Link] = None
    android_store: Optional[android_store_asset.AndroidStore] = None
    ios_store: Optional[ios_store_asset.IOSStore] = None
    android_aab: Optional[android_aab_asset.AndroidAab] = None
    android_apk: Optional[android_apk_asset.AndroidApk] = None
    ios_ipa: Optional[ios_ipa_asset.IOSIpa] = None
    api_schema: Optional[api_schema_asset.ApiSchema] = None

    def to_proto(self) -> bytes:
        data = {
            k: (v.__dict__ if isinstance(v, asset.Asset) else v)
            for k, v in self.__dict__.items()
        }
        return serializer.serialize(self.selector, data).SerializeToString()

    @property
    def proto_field(self) -> str:
        return "risk"

    def __str__(self) -> str:
        return f"Risk({self.rating}: {self.description})"
