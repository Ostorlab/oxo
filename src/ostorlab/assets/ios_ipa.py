"""iOS .IPA asset."""
import dataclasses
import io
from ostorlab.assets import asset


@dataclasses.dataclass
class IOSIpa(asset.Asset):
    """IOS .IPA target asset."""
    file: io.FileIO
