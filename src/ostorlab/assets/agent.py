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

        def to_str(value: Any) -> str:
            if type(value) is bytes:
                return value.decode()
            else:
                return str(value)

        key = data.get("key")
        if key is None:
            raise ValueError("key is missing.")
        args = {}
        version = data.get("version")
        if version is not None:
            args["version"] = to_str(version)
        docker_location = data.get("docker_location")
        if docker_location is not None:
            args["docker_location"] = to_str(docker_location)
        yaml_file_location = data.get("yaml_file_location")
        if yaml_file_location is not None:
            args["yaml_file_location"] = to_str(yaml_file_location)
        return cls(key, **args)

    @property
    def proto_field(self) -> str:
        return "agent"
