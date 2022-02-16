"""IPv4 address asset."""
import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.ip.v4')
class IPv4(asset.Asset):
    """IPv4 Address target asset."""
    host: str
    version: int = 4
    mask: Optional[str] = None

    def __str__(self):
        return f'{self.host}/{self.mask}'
