"""IPv4 address asset."""

import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.ip.v4")
class IPv4(asset.Asset):
    """IPv4 Address target asset."""

    def __init__(
        self, host: str, version: Optional[int] = 4, mask: Optional[str] = None
    ):
        self.host = host
        self.version = version
        self.mask = mask

    def __str__(self) -> str:
        return f"{self.host}/{self.mask}"

    @property
    def proto_field(self) -> str:
        return "ipv4"
