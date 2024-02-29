"""Agent and Agent group definitions and settings dataclasses."""

import dataclasses
import io
from typing import List, Optional, Dict, Any

from ostorlab.agent.schema import loader
from ostorlab.utils import defintions


@dataclasses.dataclass
class AgentDefinition:
    """Data class holding attributes of an agent."""

    name: str
    in_selectors: List[str] = dataclasses.field(default_factory=list)
    out_selectors: List[str] = dataclasses.field(default_factory=list)
    args: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    constraints: List[str] = dataclasses.field(default_factory=list)
    mounts: List[str] = dataclasses.field(default_factory=list)
    restart_policy: str = ""
    mem_limit: int = None
    open_ports: List[defintions.PortMapping] = dataclasses.field(default_factory=list)
    restrictions: List[str] = dataclasses.field(default_factory=list)
    version: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    license: Optional[str] = None
    durability: str = "published"
    docker_file_path: str = "Dockerfile"
    docker_build_root: str = "."
    image: str = None
    service_name: str = None
    caps: Optional[List[str]] = None

    @classmethod
    def from_yaml(cls, file: io.TextIOWrapper) -> "AgentDefinition":
        """Constructs an agent definition from a yaml definition file.

        Args:
            file: Yaml file.

        Returns:
            Agent definition.
        """
        definition: Dict[str, Any] = loader.load_agent_yaml(file)
        return cls(
            name=definition.get("name"),
            in_selectors=definition.get("in_selectors"),
            out_selectors=definition.get("out_selectors"),
            args=definition.get("args", []),
            constraints=definition.get("constraints", []),
            mounts=definition.get("mounts", []),
            restart_policy=definition.get("restart_policy", ""),
            mem_limit=definition.get("mem_limit"),
            open_ports=definition.get("open_ports", []),
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
        )
