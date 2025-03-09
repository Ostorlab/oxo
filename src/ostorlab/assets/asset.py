"""Abstract Asset class to define the scan target and its properties."""

import abc
from typing import Callable, Any, Type

from ostorlab import exceptions
from ostorlab.agent.message import serializer


class MissingTargetSelector(exceptions.OstorlabError):
    """Missing asset selector definition."""


class UnknownSelector(exceptions.OstorlabError):
    """Unknown selector value."""


def from_dict_factory(slctr: str, data: dict[str, Any]) -> "Asset":
    """Factory to create asset objects from a dictionary."""
    if "v3.asset.file" == slctr:
        from ostorlab.assets import file as file_asset

        return file_asset.File.from_dict(data)
    if "v3.asset.file.android.apk" == slctr:
        from ostorlab.assets import android_apk

        return android_apk.AndroidApk.from_dict(data)
    if "v3.asset.file.android.aab" == slctr:
        from ostorlab.assets import android_aab

        return android_aab.AndroidAab.from_dict(data)
    if "v3.asset.file.ios.ipa" == slctr:
        from ostorlab.assets import ios_ipa

        return ios_ipa.IOSIpa.from_dict(data)
    if "v3.asset.file.ios.testflight" == slctr:
        from ostorlab.assets import ios_testflight

        return ios_testflight.IOSTestflight.from_dict(data)
    if "v3.asset.file.api_schema" == slctr:
        from ostorlab.assets import api_schema

        return api_schema.ApiSchema.from_dict(data)
    if "v3.asset.agent" in slctr:
        from ostorlab.assets import agent as agent_asset

        return agent_asset.Agent.from_dict(data)
    if "v3.asset.store.android_store" == slctr:
        from ostorlab.assets import android_store

        return android_store.AndroidStore.from_dict(data)
    if "v3.asset.store.ios_store" == slctr:
        from ostorlab.assets import ios_store

        return ios_store.IOSStore.from_dict(data)
    if "v3.asset.domain_name" == slctr:
        from ostorlab.assets import domain_name

        return domain_name.DomainName.from_dict(data)
    if "v3.asset.ip" == slctr:
        from ostorlab.assets import ip as ip_asset

        return ip_asset.IP.from_dict(data)
    if "v3.asset.ip.v4" == slctr:
        from ostorlab.assets import ipv4 as ipv4_asset

        return ipv4_asset.IPv4.from_dict(data)
    if "v3.asset.ip.v6" == slctr:
        from ostorlab.assets import ipv6 as ipv6_asset

        return ipv6_asset.IPv6.from_dict(data)
    if "v3.asset.link" == slctr:
        from ostorlab.assets import link as link_asset

        return link_asset.Link.from_dict(data)

    raise UnknownSelector(
        f"Could not create asset object due to unknown selector: {slctr}"
    )


class Asset(abc.ABC):
    """Abstract Asset class to define the scan target and its properties."""

    selector: str

    def to_proto(self) -> Any:
        if self.selector is None:
            raise MissingTargetSelector()
        return serializer.serialize(self.selector, self.__dict__).SerializeToString()

    @property
    def proto_field(self) -> str:
        return "asset"


def selector(target: str) -> Callable[[Type[Asset]], Type[Asset]]:
    """Decorator to define an asset selector for serialization.

    Args:
        target: Target selector.

    Returns:
        Selector initializer function.
    """

    def _selector_initializer(asset: Type[Asset]) -> Type[Asset]:
        """Set asset selector."""
        asset.selector = target
        return asset

    return _selector_initializer
