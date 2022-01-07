"""Runtime are in charge of running scan as defines by a set of agents, agent group and a target asset."""
import abc
import dataclasses

from typing import List
from ostorlab.assets import asset as base_asset
from ostorlab.runtimes import definitions


@dataclasses.dataclass
class Scan:
    """Scan object."""
    # TODO(alaeddine): temporary object definition that needs to be refined.
    id: str
    application: str
    version: str
    platform: str
    plan: str
    created_time: str
    progress: str
    risk: str


class Runtime(abc.ABC):
    """Runtime is in charge of preparing the environment to trigger a scan."""

    @abc.abstractmethod
    def can_run(self, agent_group_definition: definitions.AgentGroupDefinition) -> bool:
        """Checks if the runtime is capable of running the provided agent run definition.

        Args:
            agent_group_definition: The agent run definition from a set of agents and agent groups.

        Returns:
            True if can run, false otherwise.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def scan(self, agent_group_definition: definitions.AgentGroupDefinition, asset: base_asset.Asset) -> None:
        """Triggers a scan using the provided agent run definition and asset target.

        Args:
            agent_group_definition: The agent run definition from a set of agents and agent groups.
            asset: The scan target asset.

        Returns:
            None
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def list(self, page: int = 1, number_elements: int = 10) -> List[Scan]:
        """Lists scans managed by runtime.

        Args:
            page: Page number for list pagination (default 1).
            number_elements: count of elements to show in the listed page (default 10).

        Returns:
            List of scan objects.
        """
        raise NotImplementedError()

