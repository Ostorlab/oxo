"""IP address asset."""

import dataclasses
import ipaddress
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.ip")
class IP(asset.Asset):
    """IP Address target asset."""

    def __init__(
        self, host: str, version: Optional[int] = None, mask: Optional[str] = None
    ):
        self.host = host
        self.version = version or ipaddress.ip_address(self.host).version
        self.mask = mask

    def __str__(self) -> str:
        return f"{self.host}/{self.mask}"
