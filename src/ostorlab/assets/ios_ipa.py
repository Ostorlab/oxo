"""iOS .IPA asset."""
import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.file.ios.ipa')
class IOSIpa(asset.Asset):
    """IOS .IPA target asset."""
    content: bytes
    path: Optional[str] = None

    def __str__(self):
        return f'iOS({self.path})'
