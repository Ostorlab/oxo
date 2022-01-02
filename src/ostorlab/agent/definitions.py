"""Agent and Agent group definitions and settings dataclasses."""
import dataclasses
import io
from typing import List, Optional

from ostorlab.agent.schema import loader


@dataclasses.dataclass
class Arg:
    """Data class holding a definition.

    The value is always bytes to support all arg values. The type is defined by the type attribute."""
    name: str
    type: str
    value: bytes


@dataclasses.dataclass
class PortMapping:
    """Data class defining a port mapping source to destination"""
    source_port: int
    destination_port: int


@dataclasses.dataclass
class AgentDefinition:
    """Data class holding attributes of an agent."""
    name: str
    in_selectors: List[str] = dataclasses.field(default_factory=list)
    out_selectors: List[str] = dataclasses.field(default_factory=list)
    args: List[Arg] = dataclasses.field(default_factory=list)
    constraints: List[str] = None
    mounts: Optional[List[str]] = None
    restart_policy: str = 'any'
    mem_limit: int = None
    open_ports: List[PortMapping] = dataclasses.field(default_factory=list)

    @classmethod
    def from_yaml(cls, file: io.FileIO) -> 'AgentDefinition':
        """Constructs an agent definition from a yaml definition file.

        Args:
            file: Yaml file.

        Returns:
            Agent definition.
        """
        definition = loader.load_agent_yaml(file)
        return cls(
            name=definition.get('name'),
            in_selectors=definition.get('in_selectors'),
            out_selectors=definition.get('out_selectors'),
            args=definition.get('args'),
            constraints=definition.get('constraints'),
            mounts=definition.get('mounts'),
            restart_policy=definition.get('restart_policy'),
            mem_limit=definition.get('mem_limit'),
            open_ports=definition.get('open_ports'),
        )
