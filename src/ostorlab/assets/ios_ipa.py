"""iOS .IPA asset."""

import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.file.ios.ipa")
class IOSIpa(asset.Asset):
    """IOS .IPA target asset."""

    content: Optional[bytes] = None
    path: Optional[str] = None
    content_url: Optional[str] = None

    def __str__(self) -> str:
        str_representation = "iOS"
        if self.path is not None:
            str_representation = f"{str_representation}:{self.path}"
        if self.content_url is not None:
            str_representation = f"{str_representation}:{self.content_url}"

        return str_representation

    @classmethod
    def from_dict(cls, data: dict[str, str | bytes]) -> "IOSIpa":
        """Constructs an IOSIpa asset from a dictionary."""

        def to_str(value: str | bytes | None) -> str | None:
            if value is None:
                return None
            if type(value) is bytes:
                value = value.decode()
            return str(value)

        path = to_str(data.get("path"))
        content_url = to_str(data.get("content_url"))
        content = data.get("content")
        return cls(path=path, content=content, content_url=content_url)

    @property
    def proto_field(self) -> str:
        return "ios_ipa"
