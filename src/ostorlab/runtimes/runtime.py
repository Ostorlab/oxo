"""Runtime are in charge of running scan as defines by a set of agents, agent group and a target asset."""
import abc

from ostorlab.runtimes import definitions
from ostorlab.assets import asset as base_asset



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
