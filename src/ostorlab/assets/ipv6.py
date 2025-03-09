"""IPv6 address asset."""

import dataclasses
from typing import Optional, Union

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
    def from_dict(cls, data: dict[str, Union[str, bytes]]) -> "IPv6":
        """Constructs an IPv6 asset from a dictionary."""

        host = data.get("host", "")
        if host == "":
            raise ValueError("host is missing.")
        args = {"host": host.decode() if type(host) is bytes else host, "version": 6}
        mask = data.get("mask")
        if mask is not None:
            args["mask"] = mask.decode() if type(mask) is bytes else mask
        return cls(**args)  # type: ignore

    @property
    def proto_field(self) -> str:
        return "ipv6"
