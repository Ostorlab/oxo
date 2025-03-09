"""Agent asset."""

import dataclasses
from typing import Optional

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
    def from_dict(cls, data: dict[str, str | bytes]):
        """Constructs an Agent asset from a dictionary."""

        def to_str(value: str | bytes | None) -> str | None:
            if value is None:
                return None
            if type(value) is bytes:
                value = value.decode()
            return str(value)

        key = to_str(data.get("key"))
        if key is None:
            raise ValueError("key cannot be None.")
        args = {
            "version": to_str(data.get("version")),
            "docker_location": to_str(data.get("docker_location")),
            "yaml_file_location": to_str(data.get("yaml_file_location")),
        }
        return cls(key, **args)

    @property
    def proto_field(self) -> str:
        return "agent"
