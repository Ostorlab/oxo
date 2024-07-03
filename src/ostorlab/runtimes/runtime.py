"""Runtime are in charge of running scan as defines by a set of agents, agent group and a target asset."""

import abc
import dataclasses
from typing import List, Optional

from ostorlab.assets import asset as base_asset
from ostorlab.cli import dumpers
from ostorlab.runtimes import definitions


@dataclasses.dataclass
class Scan:
    """Scan object."""

    id: str
    created_time: str
    progress: Optional[str]
    asset: Optional[str] = None


class Runtime(abc.ABC):
    """Runtime is in charge of preparing the environment to trigger a scan."""

    follow: bool

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
    def scan(
        self,
        title: str,
        agent_group_definition: definitions.AgentGroupDefinition,
        assets: Optional[List[base_asset.Asset]],
    ) -> None:
        """Triggers a scan using the provided agent run definition and asset target.

        Args:
            title: Scan title
            agent_group_definition: The agent run definition from a set of agents and agent groups.
            assets: The scan target assets.

        Returns:
            None
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def stop(self, scan_id: str) -> None:
        """Stops a scan with the given id.

        Args:
            scan_id: The scan or universe id.

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

    @abc.abstractmethod
    def install(self) -> None:
        """Run runtime installation routine.

        Returns:
            None
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def dump_vulnz(self, scan_id: int, dumper: dumpers.VulnzDumper):
        """Dump vulnerabilities to a file in a specific format.
        Returns:
        None
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def link_agent_group_scan(
        self,
        scan,
        agent_group_definition: definitions.AgentGroupDefinition,
    ) -> None:
        """Link the agent group to the scan in the database.

        Args:
            scan: The scan object.
            agent_group_definition: The agent group definition.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def link_assets_scan(self, scan_id: int, assets: List[base_asset.Asset]) -> None:
        """Link the assets to the scan in the database.

        Args:
            scan_id: The scan id.
            assets: The list of assets.
        """
        raise NotImplementedError()
