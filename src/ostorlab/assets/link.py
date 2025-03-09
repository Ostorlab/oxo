"""Link asset."""

import dataclasses

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
    def from_dict(cls, data: dict[str, str | bytes]) -> "Link":
        """Constructs a Link asset from a dictionary."""

        def to_str(value: str | bytes) -> str:
            if type(value) is bytes:
                value = value.decode()
            return str(value)

        url = to_str(data.get("url", ""))
        if url == "":
            raise ValueError("url is missing.")
        method = to_str(data.get("method", ""))
        if method == "":
            raise ValueError("method is missing.")
        return Link(url=url, method=method)

    @property
    def proto_field(self) -> str:
        return "link"
