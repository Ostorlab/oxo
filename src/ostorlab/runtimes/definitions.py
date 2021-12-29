"""Agent and Agent group definitions and settings dataclasses."""
import dataclasses
import io
from typing import List, Optional, Dict, Any

from ostorlab.agent.schema import loader


@dataclasses.dataclass
class AgentDefinition:
    """Data class holding attributes of an agent."""
    name: str
    in_selectors: List[str] = dataclasses.field(default_factory=list)
    out_selectors: List[str] = dataclasses.field(default_factory=list)
    args: List[Any] = dataclasses.field(default_factory=list)
    constraints: List[str] = None
    mounts: Optional[List[str]] = None
    restart_policy: str = 'any'
    mem_limit: int = None
    open_ports: Optional[Dict[int, int]] = None

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


@dataclasses.dataclass
class AgentInstanceSettings:
    """Agent instance lists the settings of running instance of an agent."""
    bus_url: str
    bus_exchange_topic: str
    args: List[Any] = dataclasses.field(default_factory=list)
    constraints: List[str] = None
    mounts: Optional[List[str]] = None
    restart_policy: str = 'any'
    mem_limit: int = None
    open_ports: Optional[Dict[int, int]] = None
    replicas: int = 1
    healthcheck_host: str = '0.0.0.0'
    healthcheck_port: int = 5000

    @classmethod
    def from_proto(cls, proto: bytes) -> 'AgentInstanceSettings':
        """Constructs an agent definition from a binary proto settings.

        Args:
            proto: binary proto settings file.

        Returns:
            AgentInstanceSettings object.
        """
        # TODO (amine): add implementation.
        raise NotImplementedError()


@dataclasses.dataclass
class AgentGroupDefinition:
    """Data class holding the attributes of an agent."""
    agents: List[AgentInstanceSettings]

    @classmethod
    def from_yaml(cls, group: io.FileIO):
        """Construct AgentGroupDefinition from yaml file.

        Args:
            group : agent group .yaml file.
        """
        del group
        agents = []
        return cls(agents)


@dataclasses.dataclass
class AgentRunDefinition:
    """Data class defining scan run agent composition and configuration."""
    agents: List[AgentInstanceSettings]
    agent_groups: List[AgentGroupDefinition]

    @property
    def applied_agents(self) -> List[AgentInstanceSettings]:
        """The list of applicable agents. The list is composed of both defined agent and agent groups.

        Returns:
            List of agents used in the current run definition.
        """
        agents = []
        agents.extend(self.agents)
        for group in self.agent_groups:
            agents.extend(group.agents)
        return agents
