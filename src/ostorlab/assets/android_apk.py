"""Android .APK asset."""
import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.file.android.apk')
class AndroidApk(asset.Asset):
    """Android .APK  target asset."""
    content: bytes
    path: Optional[str] = None

    def __str__(self):
        return f'Android APK({self.path})'
