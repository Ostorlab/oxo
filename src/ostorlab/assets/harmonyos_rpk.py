"""HarmonyOS .RPK-like asset."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.file.harmonyos.rpk")
class HarmonyOSRpk(asset.Asset):
    """HarmonyOS RPK target asset."""

    content: bytes | None = None
    path: str | None = None
    content_url: str | None = None

    def __str__(self) -> str:
        str_representation = "HarmonyOS RPK"
        if self.path is not None:
            str_representation = f"{str_representation}:{self.path}"
        if self.content_url is not None:
            str_representation = f"{str_representation}:{self.content_url}"

        return str_representation

    @property
    def proto_field(self) -> str:
        return "harmonyos_rpk"
