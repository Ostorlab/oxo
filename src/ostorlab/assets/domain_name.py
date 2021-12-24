"""Domain name asset definition."""
import dataclasses

from ostorlab import assets


@dataclasses.dataclass
class DomainName(assets.Asset):
    """Domain Name target asset per RFC 1034 and 1035."""
    name: str
