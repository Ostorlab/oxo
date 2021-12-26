"""Android .AAB asset."""
import dataclasses
import io
from ostorlab import assets


@dataclasses.dataclass
class AndroidAab(assets.Asset):
    """Android .AAB target asset."""
    file: io.FileIO
