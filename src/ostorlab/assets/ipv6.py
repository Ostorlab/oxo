"""IPv6 address asset."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.ip.v6")
class IPv6(asset.Asset):
    """IPv6 Address target asset."""

    host: str
    version: int = 6
    mask: str | None = None

    def __str__(self) -> str:
        return f"{self.host}/{self.mask}"

    @property
    def proto_field(self) -> str:
        return "ipv6"
