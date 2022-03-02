"""Domain name asset definition."""
import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.domain_name')
class DomainName(asset.Asset):
    """Domain Name target asset per RFC 1034 and 1035."""
    name: str

    def __str__(self):
        return self.name
