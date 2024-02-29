"""Domain name asset definition."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.domain_name")
class DomainName(asset.Asset):
    """Domain Name target asset per RFC 1034 and 1035."""

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

    @property
    def proto_field(self) -> str:
        return "domain_name"
