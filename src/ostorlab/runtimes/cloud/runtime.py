"""Remote runtime runs on Ostorlab cloud.

The remote runtime provides capabilities identical to local runtime with extra features, like data persistence,
improved data visualization, automated scaling for improved performance, agent improved data warehouse for improved
detection and several other improvements.
"""

from typing import List

import markdownify
import rich
from rich import markdown, panel

from ostorlab.apis import scan_list
from ostorlab.apis import scan_stop
from ostorlab.apis import scan_vulnz
from ostorlab.apis import vulnz_describe
from ostorlab.apis import vulnz_list
from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis.runners import runner
from ostorlab.assets import asset as base_asset
from ostorlab.cli import console as cli_console
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime
from ostorlab.utils import styles

console = cli_console.Console()


class CloudRuntime(runtime.Runtime):
    """Cloud runtime runs agents from Ostorlab Cloud."""

    def __init__(self, *args, **kwargs) -> None:
        """cloud runtime instance running on Ostorlab cloud.
        cloud runtime communicates over a GraphQL API.
        """
        super().__init__()
        del args, kwargs

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

    def stop(self, scan_id: int) -> None:
        """Stops a scan.

        Args:
            scan_id: The id of the scan to stop.
        """
        try:
            api_runner = authenticated_runner.AuthenticatedAPIRunner()
            response = api_runner.execute(scan_stop.ScanStopAPIRequest(scan_id))
            if response.get('errors') is not None:
                console.error(f'Scan with id {scan_id} not found')
            else:
                console.success('Scan stopped successfully')
        except runner.Error:
            console.error('Could not stop scan.')

    def list(self, page: int = 1, number_elements: int = 10) -> List[runtime.Scan]:
        """Lists scans managed by runtime.

        Args:
            page: Page number for list pagination (default 1).
            number_elements: count of elements to show in the listed page (default 10).

        Returns:
            List of scan objects.
        """
        try:
            api_runner = authenticated_runner.AuthenticatedAPIRunner()
            response = api_runner.execute(scan_list.ScansListAPIRequest(page, number_elements))
            scans = response['data']['scans']['scans']

            return [
                runtime.Scan(
                    id=scan['id'],
                    asset=scan['assetType'],
                    created_time=scan['createdTime'],
                    progress=scan['progress'],
                ) for scan in scans
            ]

        except runner.Error:
            console.error('Could not fetch scans.')

    def install(self) -> None:
        """No installation action.

        Returns:
            None
        """
        pass

    def list_vulnz(self, scan_id: int):
        try:
            api_runner = authenticated_runner.AuthenticatedAPIRunner()
            response = api_runner.execute(vulnz_list.VulnzListAPIRequest(scan_id))
            vulnerabilities = response['data']['scan']['kbVulnerabilities']
            vulnz_list_table = []
            for vulnerability in vulnerabilities:
                vulnz_list_table.append({
                    'id': str(vulnerability['kb']['id']),
                    'highestRiskRating': styles.style_risk(vulnerability['highestRiskRating'].upper()),
                    'cvss_v3_vector': vulnerability['kb']['cvssV3Vector'],
                    'title': vulnerability['kb']['title'],
                    'short_description': markdown.Markdown(vulnerability['kb']['shortDescription']),
                })
            columns = {
                'Id': 'id',
                'Title': 'title',
                'highest Risk Rating': 'highestRiskRating',
                'CVSS V3 Vector': 'cvss_v3_vector',
                'Short Description': 'short_description',
            }
            title = f'Scan {scan_id}: Found {len(vulnz_list_table)} vulnerabilities.'
            console.table(columns=columns, data=vulnz_list_table, title=title)
        except runner.Error:
            console.error(f'scan with id {scan_id} does not exist.')

    def _print_vulnerability(self, vulnerability):
        """Print vulnerability details"""
        if vulnerability is None:
            return

        vulnz_list_data = [
            {'id': str(vulnerability['id']),
             'risk_rating': styles.style_risk(vulnerability['customRiskRating'].upper()),
             'cvss_v3_vector': vulnerability['detail']['cvssV3Vector'],
             'title': vulnerability['detail']['title'],
             'short_description': markdown.Markdown(vulnerability['detail']['shortDescription']),
             }
        ]
        columns = {
            'Id': 'id',
            'Title': 'title',
            'Risk rating': 'risk_rating',
            'CVSS V3 Vector': 'cvss_v3_vector',
            'Short Description': 'short_description',
        }
        title = f'Describing vulnerability {vulnerability["id"]}'
        console.table(columns=columns, data=vulnz_list_data, title=title)
        rich.print(panel.Panel(markdown.Markdown(vulnerability['detail']['description']), title='Description'))
        rich.print(panel.Panel(markdown.Markdown(vulnerability['detail']['recommendation']), title='Recommendation'))
        rich.print(panel.Panel(markdown.Markdown(markdownify.markdownify(vulnerability['technicalDetail'])),
                               title='Technical details'))

    def describe_vuln(self, scan_id: int, vuln_id: int):
        try:
            vulnerabilities = []
            api_runner = authenticated_runner.AuthenticatedAPIRunner()
            if vuln_id is not None:
                response = api_runner.execute(vulnz_describe.VulnDescribeAPIRequest(vuln_id))
                vulnerability = response['data']['0']
                vulnerabilities.append(vulnerability)
                console.success('Vulnerabilities listed successfully.')
            elif scan_id is not None:
                response = api_runner.execute(scan_vulnz.ScanVulnzDescribeAPIRequest(scan_id))
                vulnerabilities = response['data']['scan']['vulnerabilities']['vulnerabilities']

            for v in vulnerabilities:
                self._print_vulnerability(v)
            console.success('Vulnerabilities listed successfully.')
        except runner.ResponseError:
            console.error(f'Scan with ID {scan_id} not found')
