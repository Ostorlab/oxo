"""Android .AAB asset."""
import dataclasses
import io
from ostorlab.assets.asset import Asset


@dataclasses.dataclass
class AndroidAab(Asset):
    """Android .AAB target asset."""
    file: io.FileIO
