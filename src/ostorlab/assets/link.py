"""Link asset."""

import dataclasses
from typing import Union

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.link")
class Link(asset.Asset):
    """Agent asset."""

    url: str
    method: str

    def __str__(self) -> str:
        return f"Link {self.url} with method {self.method}"

    @classmethod
    def from_dict(cls, data: dict[str, Union[str, bytes]]) -> "Link":
        """Constructs a Link asset from a dictionary."""

        url = data.get("url", "")
        if url == "":
            raise ValueError("url is missing.")
        method = data.get("method", "")
        if method == "":
            raise ValueError("method is missing.")
        return cls(
            url=url.decode() if type(url) is bytes else url,  # type: ignore
            method=method.decode() if type(method) is bytes else method,  # type: ignore
        )

    @property
    def proto_field(self) -> str:
        return "link"
