"""Runtime are in charge of running scan as defines by a set of agents, agent group and a target asset."""
import abc
import dataclasses
from typing import List, Iterable, Optional, Dict
import io
from ostorlab import assets


@dataclasses.dataclass
class AgentDefinition:
    """Data class holding attributes of an agent."""
    name: str
    path: str
    container_image: str
    args: Iterable = ()
    constraints: List[str] = None
    mounts: Iterable = ()
    restart_policy: str = 'any'
    mem_limit: int = None
    open_ports: Optional[Dict[int, int]] = None
    replicas: int = 1
    pull_image: bool = False
    bus_username: str = 'username'
    bus_password: str = 'password'

    @classmethod
    def from_agent_key(cls, agent_key):
        """Construct AgentDefinition from agent_key

        Args:
            agent_key: agent key
        """

        # TODO(mohsine):implement reading agent AgentDefinition using agent_key
        name = ''
        path = ''
        container_image = ''
        return cls(name, path, container_image)


@dataclasses.dataclass
class AgentGroupDefinition:
    """Data class holding the attributes of an agent."""
    agents: List[AgentDefinition]

    @classmethod
    def from_file(cls, group: io.FileIO):
        """Construct AgentGroupDefinition from yaml file.

        Args:
            group : agent group .yaml file.
        """
        return cls()


@dataclasses.dataclass
class AgentRunDefinition:
    """Data class defining scan run agent composition and configuration."""
    agents: List[AgentDefinition]
    agent_groups: List[AgentGroupDefinition]

    @property
    def applied_agents(self) -> List[AgentDefinition]:
        """The list of applicable agents. The list is composed of both defined agent and agent groups.

        Returns:
            List of agents used in the current run definition.
        """
        agents = []
        agents.extend(self.agents)
        for group in self.agent_groups:
            agents.extend(group.agents)
        return agents


class Runtime(abc.ABC):
    """Runtime is in charge of preparing the environment to trigger a scan."""

    @abc.abstractmethod
    def can_run(self, agent_run_definition: AgentRunDefinition) -> bool:
        """Checks if the runtime is capable of running the provided agent run definition.

        Args:
            agent_run_definition: The agent run definition from a set of agents and agent groups.

        Returns:
            True if can run, false otherwise.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def scan(self, agent_run_definition: AgentRunDefinition, asset: assets.Asset) -> None:
        """Triggers a scan using the provided agent run definition and asset target.

        Args:
            agent_run_definition: The agent run definition from a set of agents and agent groups.
            asset: The scan target asset.

        Returns:
            None
        """
        raise NotImplementedError()
