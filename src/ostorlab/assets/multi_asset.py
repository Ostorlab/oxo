"""Multi-asset target bundling several assets into a single proto message."""

import dataclasses
from typing import Any, List, Union

from ostorlab.agent.message.proto.v3.asset.multi_asset import multi_asset_pb2
from ostorlab.assets import android_aab as android_aab_asset
from ostorlab.assets import android_apk as android_apk_asset
from ostorlab.assets import android_store as android_store_asset
from ostorlab.assets import asset
from ostorlab.assets import ios_ipa as ios_ipa_asset
from ostorlab.assets import ios_store as ios_store_asset
from ostorlab.assets import ipv4 as ipv4_asset
from ostorlab.assets import ipv6 as ipv6_asset
from ostorlab.assets import link as link_asset

_MOBILE_ASSET_TYPES = (
    android_store_asset.AndroidStore,
    ios_store_asset.IOSStore,
    android_apk_asset.AndroidApk,
    android_aab_asset.AndroidAab,
    ios_ipa_asset.IOSIpa,
)

FileAsset = Union[
    android_apk_asset.AndroidApk,
    android_aab_asset.AndroidAab,
    ios_ipa_asset.IOSIpa,
]


@dataclasses.dataclass
@asset.selector("v3.asset.multi_asset")
class MultiAsset(asset.Asset):
    """Multi-asset target bundling several assets into a single proto message."""

    targets: List[asset.Asset]

    def __str__(self) -> str:
        return f"Multi asset ({len(self.targets)} targets)"

    def to_proto(self) -> bytes:
        """Serialize the bundled targets into a single multi-asset proto message.

        File and IP based assets are appended to their repeated fields, while the
        single mobile asset is set on the ``mobile_asset`` oneof.

        Returns:
            The serialized ``multi_asset`` proto message.

        Raises:
            ValueError: If a target type has no multi-asset proto representation, or
                if more than one mobile asset is present (the proto oneof holds one).
        """
        message = multi_asset_pb2.Message()
        has_mobile_asset = False
        for target in self.targets:
            if isinstance(target, _MOBILE_ASSET_TYPES) is True:
                if has_mobile_asset is True:
                    raise ValueError(
                        "A multi-asset message supports a single mobile asset."
                    )
                _set_mobile_asset(message, target)
                has_mobile_asset = True
            else:
                _append_target(message, target)
        return bytes(message.SerializeToString())

    @property
    def proto_field(self) -> str:
        return "multi_asset"


def _set_mobile_asset(message: Any, target: asset.Asset) -> None:
    """Set the single mobile asset on the multi-asset ``mobile_asset`` oneof.

    Raises:
        ValueError: If the mobile asset type is not supported.
    """
    if isinstance(target, android_store_asset.AndroidStore):
        message.android_package_name.package_name = target.package_name
    elif isinstance(target, ios_store_asset.IOSStore):
        message.ios_bundle_id.bundle_id = target.bundle_id
    elif isinstance(target, android_apk_asset.AndroidApk):
        _set_file_fields(message.android_apk, target)
    elif isinstance(target, android_aab_asset.AndroidAab):
        _set_file_fields(message.android_aab, target)
    elif isinstance(target, ios_ipa_asset.IOSIpa):
        _set_file_fields(message.ios_ipa, target)
    else:
        raise ValueError(f"Unsupported mobile asset type: {type(target).__name__}.")


def _append_target(message: Any, target: asset.Asset) -> None:
    """Append a non-mobile target to its repeated multi-asset field.

    Raises:
        ValueError: If the target type has no multi-asset proto representation.
    """
    if isinstance(target, ipv4_asset.IPv4):
        _set_ip_fields(message.ipv4s.add(), target)
    elif isinstance(target, ipv6_asset.IPv6):
        _set_ip_fields(message.ipv6s.add(), target)
    elif isinstance(target, link_asset.Link):
        message.urls.add(url=target.url, method=target.method)
    else:
        raise ValueError(
            f"Target type {type(target).__name__} has no multi-asset representation."
        )


def _set_ip_fields(
    ip_message: Any, target: Union[ipv4_asset.IPv4, ipv6_asset.IPv6]
) -> None:
    """Copy host, mask and version from an IP asset onto its proto message."""
    ip_message.host = target.host
    ip_message.version = target.version
    if target.mask is not None:
        ip_message.mask = target.mask


def _set_file_fields(file_message: Any, target: FileAsset) -> None:
    """Copy content, path and content url from a file asset onto its proto message."""
    if target.content is not None:
        file_message.content = target.content
    if target.path is not None:
        file_message.path = target.path
    if target.content_url is not None:
        file_message.content_url = target.content_url
