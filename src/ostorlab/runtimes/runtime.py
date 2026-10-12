"""Runtime are in charge of running scan as defines by a set of agents, agent group and a target asset."""

from __future__ import annotations

import abc
import builtins
import dataclasses
import datetime
import typing

from ostorlab.assets import asset as base_asset
from ostorlab.cli import dumpers
from ostorlab.runtimes import definitions

if typing.TYPE_CHECKING:
    from ostorlab.runtimes.local.models import models
    from ostorlab.utils import risk_rating


@dataclasses.dataclass
class Scan:
    """Scan object."""

    id: str | int
    created_time: typing.Optional[str | datetime.datetime]
    progress: typing.Optional[str]
    asset: typing.Optional[str] = None
    risk_rating: typing.Optional[str | risk_rating.RiskRating] = None


ScanIdentifier_contra = typing.TypeVar("ScanIdentifier_contra", contravariant=True)


class Runtime(abc.ABC, typing.Generic[ScanIdentifier_contra]):
    """Runtime is in charge of preparing the environment to trigger a scan."""

    follow: typing.Collection[str]
    timeout: typing.Optional[int] = None
    init_sleep: typing.Optional[int] = None
    has_tracker: bool = True

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
        title: typing.Optional[str],
        agent_group_definition: definitions.AgentGroupDefinition,
        assets: typing.Optional[typing.Sequence[base_asset.Asset]],
    ) -> typing.Optional[models.Scan]:
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
    def stop(self, scan_id: ScanIdentifier_contra) -> typing.Optional[bool]:
        """Stops a scan with the given id.

        Args:
            scan_id: The scan or universe id.

        Returns:
            None
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def list(
        self,
        page: int = 1,
        number_elements: int = 10,
        state: typing.Optional[str] = None,
    ) -> typing.Optional[builtins.list[Scan]]:
        """Lists scans managed by runtime.

        Args:
            page: Page number for list pagination (default 1).
            number_elements: count of elements to show in the listed page (default 10).
            state: Filter scans by state.

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
    def dump_vulnz(self, scan_id: int, dumper: dumpers.VulnzDumper) -> None:
        """Dump vulnerabilities to a file in a specific format.
        Returns:
        None
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def link_agent_group_scan(
        self,
        scan: models.Scan,
        agent_group_definition: definitions.AgentGroupDefinition,
    ) -> None:
        """Link the agent group to the scan in the database.

        Args:
            scan: The scan object.
            agent_group_definition: The agent group definition.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def link_assets_scan(
        self, scan_id: int, assets: typing.Optional[builtins.list[base_asset.Asset]]
    ) -> None:
        """Link the assets to the scan in the database.

        Args:
            scan_id: The scan id.
            assets: The list of assets.
        """
        raise NotImplementedError()
