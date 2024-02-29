"""Link asset."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.link")
class Link(asset.Asset):
    """Agent asset."""

    def __init__(self, url: str, method: str):
        self.url = url
        self.method = method

    def __str__(self) -> str:
        return f"Link {self.url} with method {self.method}"

    @property
    def proto_field(self) -> str:
        return "link"
