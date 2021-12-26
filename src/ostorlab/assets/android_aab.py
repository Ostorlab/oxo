"""Android .AAB asset."""
import dataclasses
import io
from ostorlab.assets import asset


@dataclasses.dataclass
class AndroidAab(asset.Asset):
    """Android .AAB target asset."""
    file: io.FileIO
