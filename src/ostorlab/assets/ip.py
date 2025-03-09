"""IP address asset."""

import dataclasses
import ipaddress
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.ip")
class IP(asset.Asset):
    """IP Address target asset."""

    host: str
    version: Optional[int] = None
    mask: Optional[str] = None

    def __post_init__(self) -> None:
        if self.version is None:
            self.version = ipaddress.ip_address(self.host).version

    @classmethod
    def from_dict(cls, data: dict[str, str | bytes]) -> "IP":
        """Constructs an IP asset from a dictionary."""

        def to_str(value: str | bytes | None) -> str | None:
            if value is None:
                return None
            if type(value) is bytes:
                value = value.decode()
            return str(value)

        host = to_str(data.get("host", ""))
        if host == "":
            raise ValueError("host is missing.")
        version = data.get("version")
        if version is not None:
            version = int(version)
        mask = to_str(data.get("mask"))
        return cls(host=host, version=version, mask=mask)

    def __str__(self) -> str:
        return f"{self.host}/{self.mask}"
