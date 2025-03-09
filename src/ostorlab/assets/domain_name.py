"""Domain name asset definition."""

import dataclasses
from typing import Union

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.domain_name")
class DomainName(asset.Asset):
    """Domain Name target asset per RFC 1034 and 1035."""

    name: str

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_dict(cls, data: dict[str, Union[str, bytes]]) -> "DomainName":
        """Constructs an DomainName asset from a dictionary."""
        name = data.get("name", "")
        if name == "":
            raise ValueError("name is missing.")
        return DomainName(name.decode() if type(name) is bytes else name)  # type: ignore

    @property
    def proto_field(self) -> str:
        return "domain_name"
