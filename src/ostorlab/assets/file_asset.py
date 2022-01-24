"""File asset."""
import dataclasses
from typing import Optional
from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.file')
class FileAsset(asset.Asset):
    """File target asset."""
    content: bytes
    