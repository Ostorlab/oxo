"""IPv6 address asset."""

import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.ip.v6")
class IPv6(asset.Asset):
    """IPv6 Address target asset."""

    host: str
    version: int = 6
    mask: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.host}/{self.mask}"

    @classmethod
    def from_dict(cls, data: dict[str, str | bytes]) -> "IPv6":
        """Constructs an IPv6 asset from a dictionary."""

        def to_str(value: str | bytes) -> str:
            if type(value) is bytes:
                value = value.decode()
            return str(value)

        host = to_str(data.get("host", ""))
        if host == "":
            raise ValueError("host is missing.")
        mask = to_str(data.get("mask", ""))
        return cls(host=host, mask=mask)

    @property
    def proto_field(self) -> str:
        return "ipv6"
