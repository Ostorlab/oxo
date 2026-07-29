"""CIDR network asset discovered during reconnaissance."""

import dataclasses
import ipaddress

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.network")
class Network(asset.Asset):
    """CIDR network discovered during reconnaissance.

    Represents a network range observed as a recon output. It is intentionally
    distinct from the active IP scan assets (`v3.asset.ip.v4`, `v3.asset.ip.v6`)
    and must not be enumerated or scanned as individual addresses.
    """

    cidr: str

    def __post_init__(self) -> None:
        self.cidr = str(ipaddress.ip_network(self.cidr, strict=False))

    def __str__(self) -> str:
        return self.cidr

    @property
    def proto_field(self) -> str:
        return "network"
