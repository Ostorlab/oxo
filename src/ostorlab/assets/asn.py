"""Autonomous System Number asset definition."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.asn")
class ASN(asset.Asset):
    """Autonomous System Number target asset, e.g. 15169."""

    asn: str

    def __str__(self) -> str:
        return self.asn

    @property
    def proto_field(self) -> str:
        return "asn"
