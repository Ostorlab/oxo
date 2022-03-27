"""Agent asset."""
import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector('v3.asset.agent')
class Agent(asset.Asset):
    """Agent asset."""
    key: str
    version: Optional[str] = None
    git_location: Optional[str] = None
    docker_location: Optional[str] = None
    yaml_file_location: Optional[str] = None

    def __str__(self):
        if self.version is not None:
            return f'Agent {self.key}:{self.version}'
        else:
            return f'Agent {self.key}'
