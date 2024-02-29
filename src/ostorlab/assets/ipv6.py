"""IPv6 address asset."""

import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.ip.v6")
class IPv6(asset.Asset):
    """IPv6 Address target asset."""

    def __init__(
        self, host: str, version: Optional[int] = 6, mask: Optional[str] = None
    ):
        self.host = host
        self.version = version
        self.mask = mask

    def __str__(self) -> str:
        return f"{self.host}/{self.mask}"

    @property
    def proto_field(self) -> str:
        return "ipv6"
