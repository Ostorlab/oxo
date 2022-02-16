"""File asset."""
import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.file')
class File(asset.Asset):
    """File target asset."""
    content: bytes
    path: Optional[str] = None

    def __str__(self):
        return f'File({self.path})'
