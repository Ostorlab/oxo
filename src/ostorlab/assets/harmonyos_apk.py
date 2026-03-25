"""HarmonyOS .APK-like asset."""

import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.file.harmonyos.apk")
class HarmonyOSApk(asset.Asset):
    """HarmonyOS APK target asset (packaged APK for HarmonyOS contexts)."""

    content: Optional[bytes] = None
    path: Optional[str] = None
    content_url: Optional[str] = None

    def __str__(self) -> str:
        str_representation = "HarmonyOS APK"
        if self.path is not None:
            str_representation = f"{str_representation}:{self.path}"
        if self.content_url is not None:
            str_representation = f"{str_representation}:{self.content_url}"

        return str_representation

    @property
    def proto_field(self) -> str:
        return "harmonyos_apk"
