"""Agent and Agent group definitions and settings dataclasses."""

import dataclasses
import io
from typing import Any

from ostorlab.agent.schema import loader
from ostorlab.utils import definitions


@dataclasses.dataclass
class AgentDefinition:
    """Data class holding attributes of an agent."""

    name: str
    in_selectors: list[str] = dataclasses.field(default_factory=list)
    out_selectors: list[str] = dataclasses.field(default_factory=list)
    args: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    constraints: list[str] = dataclasses.field(default_factory=list)
    mounts: list[str] = dataclasses.field(default_factory=list)
    volumes: list[definitions.Volume] = dataclasses.field(default_factory=list)
    restart_policy: str = ""
    mem_limit: int | None = None
    open_ports: list[definitions.PortMapping] = dataclasses.field(default_factory=list)
    restrictions: list[str] = dataclasses.field(default_factory=list)
    version: str | None = None
    description: str | None = None
    source: str | None = None
    license: str | None = None
    durability: str = "published"
    docker_file_path: str = "Dockerfile"
    docker_build_root: str = "."
    image: str | None = None
    service_name: str | None = None
    caps: list[str] | None = None
    supported_architectures: list[str] | None = None

    @classmethod
    def from_yaml(cls, file: io.TextIOWrapper) -> "AgentDefinition":
        """Constructs an agent definition from a yaml definition file.

        Args:
            file: Yaml file.

        Returns:
            Agent definition.
        """
        definition: dict[str, Any] = loader.load_agent_yaml(file)
        return cls(
            name=definition.get("name", ""),
            in_selectors=definition.get("in_selectors", []),
            out_selectors=definition.get("out_selectors", []),
            args=definition.get("args", []),
            constraints=definition.get("constraints", []),
            mounts=definition.get("mounts", []),
            volumes=[
                definitions.Volume(
                    name=v["name"],
                    path=v["path"],
                    read_only=v.get("read_only", True),
                )
                for v in definition.get("volumes", [])
            ],
            restart_policy=definition.get("restart_policy", ""),
            mem_limit=definition.get("mem_limit"),
            open_ports=[
                definitions.PortMapping(
                    source_port=p.get("src_port"),
                    destination_port=p.get("dest_port"),
                )
                for p in definition.get("open_ports", [])
            ],
            restrictions=definition.get("restrictions", []),
            version=definition.get("version"),
            description=definition.get("description"),
            source=definition.get("source"),
            license=definition.get("license"),
            durability=definition.get("durability", "published"),
            docker_file_path=definition.get("docker_file_path", "Dockerfile"),
            docker_build_root=definition.get("docker_build_root", "."),
            image=definition.get("image"),
            service_name=definition.get("service_name"),
            caps=definition.get("caps"),
            supported_architectures=definition.get("supported_architectures"),
        )
