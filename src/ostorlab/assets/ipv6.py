"""IPv6 address asset."""
import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.ip.v6')
class IPv6(asset.Asset):
    """IPv6 Address target asset."""
    host: str
    version: int = 6
    mask: Optional[str] = None

    def __str__(self):
        return f'{self.host}/{self.mask}'
