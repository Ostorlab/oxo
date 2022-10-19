"""Android .AAB asset."""
import dataclasses
from typing import Optional

from ostorlab.assets import asset


@asset.selector('v3.asset.file.android.aab')
@dataclasses.dataclass
class AndroidAab(asset.Asset):
    """Android .AAB target asset."""

    def __init__(self, content: bytes, path: Optional[str] = None):
        self.content = content
        self.path = path

    def __str__(self) -> str:
        return f'Android AAB({self.path})'

    @property
    def proto_field(self) -> str:
        return 'android_aab'
