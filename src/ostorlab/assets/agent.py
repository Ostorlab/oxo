"""Agent asset."""

import dataclasses
from typing import Optional, Any

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.agent")
class Agent(asset.Asset):
    """Agent asset."""

    key: str
    version: Optional[str] = None
    git_location: Optional[str] = None
    docker_location: Optional[str] = None
    yaml_file_location: Optional[str] = None

    def __str__(self) -> str:
        if self.version is not None:
            return f"Agent {self.key}:{self.version}"
        else:
            return f"Agent {self.key}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Agent":
        """Constructs an Agent asset from a dictionary."""

        key = data.get("key")
        if key is None:
            raise ValueError("key is missing.")
        args = {"key": key.decode() if type(key) is bytes else key}
        version = data.get("version")
        if version is not None:
            args["version"] = version.decode() if type(version) is bytes else version
        docker_location = data.get("docker_location")
        if docker_location is not None:
            args["docker_location"] = (
                docker_location.decode()
                if type(docker_location) is bytes
                else docker_location
            )
        yaml_file_location = data.get("yaml_file_location")
        if yaml_file_location is not None:
            args["yaml_file_location"] = (
                yaml_file_location.decode()
                if type(yaml_file_location) is bytes
                else yaml_file_location
            )
        return cls(**args)

    @property
    def proto_field(self) -> str:
        return "agent"
