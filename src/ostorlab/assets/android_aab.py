"""Android .AAB asset."""

import dataclasses
from typing import Optional

from ostorlab.assets import asset


@asset.selector("v3.asset.file.android.aab")
@dataclasses.dataclass
class AndroidAab(asset.Asset):
    """Android .AAB target asset."""

    def __init__(
        self,
        content: Optional[bytes] = None,
        path: Optional[str] = None,
        content_url: Optional[str] = None,
    ):
        self.content = content
        self.path = path
        self.content_url = content_url

    def __str__(self) -> str:
        str_representation = "Android AAB"
        if self.path is not None:
            str_representation = f"{str_representation}:{self.path}"
        if self.content_url is not None:
            str_representation = f"{str_representation}:{self.content_url}"

        return str_representation

    @property
    def proto_field(self) -> str:
        return "android_aab"
