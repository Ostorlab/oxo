"""Link asset."""
import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.link')
class Link(asset.Asset):
    """Agent asset."""
    url: str
    method: str

    def __str__(self):
        return f'Link {self.url} with method {self.method}'
