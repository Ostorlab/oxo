"""iOS .IPA asset."""
import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.file.ios.ipa')
class IOSIpa(asset.Asset):
    """IOS .IPA target asset."""

    def __init__(self, content: bytes, path: Optional[str] = None):
        self.content = content
        self.path = path

    def __str__(self) -> str:
        return f'iOS({self.path})'

    @property
    def proto_field(self) -> str:
        return 'ios_ipa'
