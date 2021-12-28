"""iOS .IPA asset."""
import dataclasses
import io
from ostorlab import assets


@dataclasses.dataclass
class IOSIpa(assets.Asset):
    """IOS .IPA target asset."""
    file: io.FileIO
