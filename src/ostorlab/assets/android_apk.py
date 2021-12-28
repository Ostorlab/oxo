"""Android .APK asset."""
import dataclasses
import io
from ostorlab import assets


@dataclasses.dataclass
class AndroidApk(assets.Asset):
    """Android .APK  target asset."""
    file: io.FileIO
