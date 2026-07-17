"""Multi asset."""

import dataclasses

from ostorlab.assets import android_aab
from ostorlab.assets import android_apk
from ostorlab.assets import android_store
from ostorlab.assets import asset
from ostorlab.assets import file
from ostorlab.assets import harmonyos_hap
from ostorlab.assets import harmonyos_store
from ostorlab.assets import ios_ipa
from ostorlab.assets import ios_store
from ostorlab.assets import ip
from ostorlab.assets import ipv4
from ostorlab.assets import ipv6
from ostorlab.assets import link
from ostorlab.assets import repository
from ostorlab.assets import repository_archive


@dataclasses.dataclass
@asset.selector("v3.asset.multi_asset")
class MultiAsset(asset.Asset):
    """Multi-asset target grouping heterogeneous assets in a single scan target."""

    files: list[file.File] = dataclasses.field(default_factory=list)
    android_package_name: android_store.AndroidStore | None = None
    ios_bundle_id: ios_store.IOSStore | None = None
    harmonyos_bundle_name: harmonyos_store.HarmonyOSStore | None = None
    android_apk: android_apk.AndroidApk | None = None
    android_aab: android_aab.AndroidAab | None = None
    ios_ipa: ios_ipa.IOSIpa | None = None
    harmonyos_hap: harmonyos_hap.HarmonyOSHap | None = None
    repositories: list[repository.Repository] = dataclasses.field(default_factory=list)
    repository_archives: list[repository_archive.RepositoryArchive] = dataclasses.field(
        default_factory=list
    )
    urls: list[link.Link] = dataclasses.field(default_factory=list)
    ips: list[ip.IP] = dataclasses.field(default_factory=list)
    ipv4s: list[ipv4.IPv4] = dataclasses.field(default_factory=list)
    ipv6s: list[ipv6.IPv6] = dataclasses.field(default_factory=list)

    def __str__(self) -> str:
        nested_assets = [
            str(nested_asset)
            for nested_asset in self._nested_assets()
            if nested_asset is not None
        ]
        return f"MultiAsset: [{', '.join(nested_assets)}]"

    def _nested_assets(self) -> list[asset.Asset | None]:
        return [
            *self.files,
            self.android_package_name,
            self.ios_bundle_id,
            self.harmonyos_bundle_name,
            self.android_apk,
            self.android_aab,
            self.ios_ipa,
            self.harmonyos_hap,
            *self.repositories,
            *self.repository_archives,
            *self.urls,
            *self.ips,
            *self.ipv4s,
            *self.ipv6s,
        ]

    @property
    def proto_field(self) -> str:
        return "multi_asset"
