"""iOS .IPA asset."""
import dataclasses
import io
from ostorlab.assets.asset import Asset


@dataclasses.dataclass
class IOSIpa(Asset):
    """IOS .IPA target asset."""
    file: io.FileIO
