"""IP address asset."""

import dataclasses
import ipaddress

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.ip")
class IP(asset.Asset):
    """IP Address target asset."""

    host: str
    version: int | None = None
    mask: str | None = None

    def __post_init__(self) -> None:
        if self.version is None:
            self.version = ipaddress.ip_address(self.host).version

    def __str__(self) -> str:
        return f"{self.host}/{self.mask}"
