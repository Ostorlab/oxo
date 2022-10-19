"""Android .APK asset."""
import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.file.android.apk')
class AndroidApk(asset.Asset):
    """Android .APK  target asset."""

    def __init__(self, content: bytes, path: Optional[str] = None):
        self.content = content
        self.path = path

    def __str__(self) -> str:
        return f'Android APK ({self.path})'

    @property
    def proto_field(self) -> str:
        return 'android_apk'
