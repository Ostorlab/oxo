import abc
import dataclasses
from typing import List, Iterable, Optional, Dict

from ostorlab.assets import Asset


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


@dataclasses.dataclass
class AgentGroupDefinition:
    """Data class holding the attributes of an agent."""


@dataclasses.dataclass
class AgentRunDefinition:
    agents: List[AgentDefinition]
    agent_groups: List[AgentGroupDefinition]


class Runtime(abc.ABC):
    """Runtime is in charge of preparing the environment to trigger a scan."""

    @abc.abstractmethod
    def can_run(self, agent_run_definition: AgentRunDefinition) -> bool:
        """Checks if the runtime is capable of running the provided agent run definition."""
        raise NotImplementedError()

    @abc.abstractmethod
    def scan(self, agent_run_definition: AgentRunDefinition, asset: Asset) -> None:
        """Triggers a scan using the provided agent run definition and asset target."""
        raise NotImplementedError()
