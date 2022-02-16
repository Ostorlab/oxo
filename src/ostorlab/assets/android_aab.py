"""Android .AAB asset."""
import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.file.android.aab')
class AndroidAab(asset.Asset):
    """Android .AAB target asset."""
    content: bytes
    path: Optional[str] = None

    def __str__(self):
        return f'Android AAB({self.path})'
