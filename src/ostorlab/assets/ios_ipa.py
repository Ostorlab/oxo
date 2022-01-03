"""iOS .IPA asset."""
import dataclasses
from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.file.ios.ipa')
class IOSIpa(asset.Asset):
    """IOS .IPA target asset."""
    content: bytes
