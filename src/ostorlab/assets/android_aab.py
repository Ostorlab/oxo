"""Android .AAB asset."""

import dataclasses
from typing import Optional, Union, cast

from ostorlab.assets import asset


@asset.selector("v3.asset.file.android.aab")
@dataclasses.dataclass
class AndroidAab(asset.Asset):
    """Android .AAB target asset."""

    content: Optional[bytes] = None
    path: Optional[str] = None
    content_url: Optional[str] = None

    def __str__(self) -> str:
        str_representation = "Android AAB"
        if self.path is not None:
            str_representation = f"{str_representation}:{self.path}"
        if self.content_url is not None:
            str_representation = f"{str_representation}:{self.content_url}"

        return str_representation

    @classmethod
    def from_dict(cls, data: dict[str, Union[str, bytes]]) -> "AndroidAab":
        """Constructs an AndroidAab asset from a dictionary."""

        args = {}
        path = data.get("path")
        if path is not None:
            args["path"] = path.decode() if type(path) is bytes else path
        content_url = data.get("content_url")
        if content_url is not None:
            args["content_url"] = (
                content_url.decode() if type(content_url) is bytes else content_url
            )
        content = data.get("content")
        if content is not None:
            args["content"] = cast(bytes, content)
        return cls(**args)  # type: ignore

    @property
    def proto_field(self) -> str:
        return "android_aab"
