"""Autonomous System Number asset."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.asn")
class ASN(asset.Asset):
    """Autonomous System Number used as a standalone scan input."""

    asn: str

    def __str__(self) -> str:
        return self.asn

    @property
    def proto_field(self) -> str:
        return "asn"
