"""Agent asset."""
from typing import Optional

from ostorlab.assets import asset


@asset.selector('v3.asset.agent')
class Agent(asset.Asset):
    """Agent asset."""

    def __init__(self, key: str, version: Optional[str] = None, git_location: Optional[str] = None,
                 docker_location: Optional[str] = None,
                 yaml_file_location: Optional[str] = None):
        self.key = key
        self.version = version
        self.git_location = git_location
        self.docker_location = docker_location
        self.yaml_file_location = yaml_file_location

    def __str__(self):
        if self.version is not None:
            return f'Agent {self.key}:{self.version}'
        else:
            return f'Agent {self.key}'
