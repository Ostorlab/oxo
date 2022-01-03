"""Android .AAB asset."""
import dataclasses
from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.file.android.aab')
class AndroidAab(asset.Asset):
    """Android .AAB target asset."""
    content: bytes
