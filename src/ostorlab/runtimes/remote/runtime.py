"""Remote runtime runs on Ostorlab cloud.

The remote runtime provides capabilities identical to local runtime with extra features, like data persistence,
improved data visualization, automated scaling for improved performance, agent improved data warehouse for improved
detection and several other improvements.
"""
from typing import List

from ostorlab.apis import runner as apis_runner
from ostorlab.apis import scan_list
from ostorlab.assets import asset as base_asset
from ostorlab.cli import console as cli_console
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime

console = cli_console.Console()


class RemoteRuntime(runtime.Runtime):
    """Remote runtime instance running on Ostorlab cloud.

    Remote runtime communicates over a GraphQL API."""

    def can_run(self, agent_group_definition: definitions.AgentGroupDefinition) -> bool:
        """Checks if the runtime is capable of running the provided agent run definition.

        Args:
            agent_group_definition: The agent run definition from a set of agents and agent groups.

        Returns:
            True if can run, false otherwise.
        """
        pass

    def scan(self, agent_group_definition: definitions.AgentGroupDefinition, asset: base_asset.Asset) -> None:
        """Triggers a scan using the provided agent run definition and asset target.

        Args:
            agent_group_definition: The agent run definition from a set of agents and agent groups.
            asset: The scan target asset.

        Returns:
            None
        """
        pass

    def list(self, page: int = 1, number_elements: int = 10) -> List[runtime.Scan]:
        """Lists scans managed by runtime.

        Args:
            page: Page number for list pagination (default 1).
            number_elements: count of elements to show in the listed page (default 10).

        Returns:
            List of scan objects.
        """
        try:
            runner = apis_runner.APIRunner()
            response = runner.execute(scan_list.ScansListAPIRequest(page, number_elements))
            scans = response['data']['scans']['scans']

            return [
                runtime.Scan(
                    id=scan['id'],
                    application=scan['packageName'],
                    version=scan['version'],
                    platform=scan['assetType'],
                    plan=scan['plan'],
                    created_time=scan['createdTime'],
                    progress=scan['progress'],
                    risk=scan['riskRating'],
                ) for scan in scans
            ]

        except apis_runner.Error:
            console.error('Could not fetch scans.')
