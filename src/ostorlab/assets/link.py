"""Link asset."""

import dataclasses
from typing import List, Optional, Dict

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.link")
class Link(asset.Asset):
    """Link asset."""

    url: str
    method: str
    body: Optional[bytes] = None
    # Headers and Cookies are dict with the keys `name` and `value`.
    extra_headers: Optional[List[Dict[str, str]]] = dataclasses.field(
        default_factory=list
    )
    cookies: Optional[List[Dict[str, str]]] = dataclasses.field(default_factory=list)

    def __str__(self) -> str:
        info = f"Link {self.url} with method {self.method}"
        if self.extra_headers is not None and len(self.extra_headers) > 0:
            info += f", headers: {self.extra_headers}"
        if self.cookies is not None and len(self.cookies) > 0:
            info += f", cookies: {self.cookies}"
        if self.body is not None:
            info += f", body: {self.body!r}"
        return info

    @property
    def proto_field(self) -> str:
        return "link"
