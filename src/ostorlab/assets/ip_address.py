"""IP address asset."""
import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.ip')
class IpAddress(asset.Asset):
    """IP Adress target asset."""
    host: str
    mask: Optional[str] = None
