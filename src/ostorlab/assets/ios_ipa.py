"""iOS .IPA asset."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.file.ios.ipa")
class IOSIpa(asset.Asset):
    """IOS .IPA target asset."""

    content: bytes | None = None
    path: str | None = None
    content_url: str | None = None

    def __str__(self) -> str:
        str_representation = "iOS"
        if self.path is not None:
            str_representation = f"{str_representation}:{self.path}"
        if self.content_url is not None:
            str_representation = f"{str_representation}:{self.content_url}"

        return str_representation

    @property
    def proto_field(self) -> str:
        return "ios_ipa"
