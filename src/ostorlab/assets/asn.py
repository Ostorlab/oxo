"""Autonomous System Number asset definition."""

import dataclasses

from ostorlab.assets import asset


def normalize(asn: str) -> str:
    """Normalize an ASN so `AS15169`, `as15169` and `15169` are all stored as `15169`, as on RE."""
    return asn.strip().upper().removeprefix("AS")


@dataclasses.dataclass
@asset.selector("v3.asset.asn")
class ASN(asset.Asset):
    """Autonomous System Number target asset, e.g. 15169."""

    asn: str

    def __post_init__(self) -> None:
        self.asn = normalize(self.asn)

    def __str__(self) -> str:
        return self.asn

    @property
    def proto_field(self) -> str:
        return "asn"
