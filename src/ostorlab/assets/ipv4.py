"""IP address asset."""
import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.ip.v4')
class IPv4(asset.Asset):
    """IP Adress target asset."""
    host: str
    version: int = 4
    mask: Optional[str] = None
