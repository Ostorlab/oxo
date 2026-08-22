"""Agent asset."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.agent")
class Agent(asset.Asset):
    """Agent asset."""

    key: str
    version: str | None = None
    git_location: str | None = None
    docker_location: str | None = None
    yaml_file_location: str | None = None

    def __str__(self) -> str:
        if self.version is not None:
            return f"Agent {self.key}:{self.version}"
        else:
            return f"Agent {self.key}"

    @property
    def proto_field(self) -> str:
        return "agent"
