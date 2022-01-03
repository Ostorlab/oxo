"""Android .APK asset."""
import dataclasses
from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.file.android.apk')
class AndroidApk(asset.Asset):
    """Android .APK  target asset."""
    content: bytes
