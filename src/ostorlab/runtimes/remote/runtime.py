from typing import List

from ostorlab.apis import runner as apis_runner
from ostorlab.apis import scan_list
from ostorlab.assets import asset as base_asset
from ostorlab.cli import console as cli_console
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime

console = cli_console.Console()


class RemoteRuntime(runtime.Runtime):

    def can_run(self, agent_group_definition: definitions.AgentGroupDefinition) -> bool:
        pass

    def scan(self, agent_group_definition: definitions.AgentGroupDefinition, asset: base_asset.Asset) -> None:
        pass

    def list(self, page: int = 1, number_elements: int = 10) -> List[runtime.Scan]:
        try:
            runner = apis_runner.APIRunner()
            with console.status('Fetching scans'):
                response = runner.execute(scan_list.ScansListAPIRequest(page, number_elements))

            scans = response['data']['scans']['scans']

            return [
                runtime.Scan(
                    id=scan['id'],
                    application=scan['packageName'],
                    version=scan['version'],
                    platform=scan['assetType'],
                    plan=scan['plan'],
                    created_time=scan['createTime'],
                    progress=scan['progress'],
                    risk=scan['riskRating'],
                ) for scan in scans
            ]

        except apis_runner.Error:
            console.error('Could not fetch scans.')
