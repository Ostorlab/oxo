"""IPv4 address asset."""

import dataclasses
from typing import Optional, Union

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.ip.v4")
class IPv4(asset.Asset):
    """IPv4 Address target asset."""

    host: str
    version: int = 4
    mask: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.host}/{self.mask}"

    @classmethod
    def from_dict(cls, data: dict[str, Union[str, bytes]]) -> "IPv4":
        """Constructs an IPv4 asset from a dictionary."""

        host = data.get("host", "")
        if host == "":
            raise ValueError("host is missing.")
        args = {"host": host.decode() if type(host) is bytes else host, "version": 4}
        mask = data.get("mask")
        if mask is not None:
            args["mask"] = mask.decode() if type(mask) is bytes else mask
        return cls(**args)  # type: ignore

    @property
    def proto_field(self) -> str:
        return "ipv4"
