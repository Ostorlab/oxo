"""IP address asset."""

import dataclasses
import ipaddress
from typing import Optional, Union

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
    def from_dict(cls, data: dict[str, Union[str, bytes]]) -> "IP":
        """Constructs an IP asset from a dictionary."""

        host = data.get("host", "")
        if host == "":
            raise ValueError("host is missing.")
        args = {"host": host.decode() if type(host) is bytes else host}
        version = data.get("version")
        if version is not None:
            args["version"] = int(version)  # type: ignore
        mask = data.get("mask")
        if mask is not None:
            args["mask"] = mask.decode() if type(mask) is bytes else mask
        return cls(**args)  # type: ignore

    def __str__(self) -> str:
        return f"{self.host}/{self.mask}"
