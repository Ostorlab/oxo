"""File asset."""
import dataclasses
from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.file')
class File(asset.Asset):
    """File target asset."""
    content: bytes
