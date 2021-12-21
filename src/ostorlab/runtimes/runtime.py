from typing import List

import abc
import dataclasses

from ostorlab.assets import Asset


@dataclasses.dataclass
class AgentRunDefinition:
    agents: List
    agent_groups: List


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

