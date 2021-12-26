"""Android .APK asset."""
import dataclasses
import io
from ostorlab.assets import asset


@dataclasses.dataclass
class AndroidApk(asset.Asset):
    """Android .APK  target asset."""
    file: io.FileIO
