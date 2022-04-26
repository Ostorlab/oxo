"""Remote runtime runs on Ostorlab cloud.

The remote runtime provides capabilities identical to local runtime with extra features, like data persistence,
improved data visualization, automated scaling for improved performance, agent improved data warehouse for improved
detection and several other improvements.
"""

from typing import List, Optional, Dict, Union

import click
import markdownify
import rich
from rich import markdown, panel

from ostorlab import configuration_manager
from ostorlab.apis import agent_details
from ostorlab.apis import agent_group
from ostorlab.apis import assets as api_assets
from ostorlab.apis import create_agent_scan
from ostorlab.apis import scan_list
from ostorlab.apis import scan_stop
from ostorlab.apis import vulnz_describe
from ostorlab.apis import vulnz_list
from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis.runners import runner
from ostorlab.assets import asset as base_asset
from ostorlab.cli import console as cli_console
from ostorlab.cli import dumpers
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime
from ostorlab.utils import styles

AgentType = Dict[str, Union[str, List]]
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
            agent_group_definition: The agent group definition of a set of agents.

        Returns:
            True if can run, false otherwise.
        """
        try:
            config_manager = configuration_manager.ConfigurationManager()

            if not config_manager.is_authenticated:
                console.error('You need to be authenticated before using the cloud runtime.')
                return False

            do_agents_exist = self._check_agents_exist(agent_group_definition)
            return do_agents_exist
        except runner.ResponseError as error_msg:
            console.error(error_msg)
            return False

    def scan(
            self,
            title: Optional[str],
            agent_group_definition: definitions.AgentGroupDefinition,
            assets: Optional[List[base_asset.Asset]]
    ) -> None:
        """Triggers a scan using the provided agent group definition and asset target.

        Args:
            title: The title of the scan.
            agent_group_definition: The agent group definition of a set of agents.
            assets: The scan target asset.

        Returns:
            None
        """
        try:
            if len(assets) > 1:
                raise NotImplementedError()
            else:
                asset = assets[0]
            # we support multiple assets for local runtime for the cloud runtime. we take just the first asset.
            api_runner = authenticated_runner.AuthenticatedAPIRunner()

            agents = self._agents_from_agent_group_def(api_runner, agent_group_definition)
            name = agent_group_definition.name
            description = agent_group_definition.description

            console.info('Creating agent group')
            agent_group_id = self._create_agent_group(api_runner, name, description, agents)

            console.info('Creating asset')
            asset_id = self._create_asset(api_runner, asset)

            console.info('Creating scan')
            self._create_scan(api_runner, asset_id, agent_group_id, title)

            console.success('Scan created successfully.')
        except runner.ResponseError as error_msg:
            console.error(error_msg)

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

    def list_vulnz(self, scan_id: int, page: int = 1, number_elements: int = 10):
        """List vulnz from the cloud using and render them in a table.

        Args:
            scan_id: scan id to list vulnz from.
            page: optional page number.
            number_elements: optional number of elements per page.
        """
        try:
            api_runner = authenticated_runner.AuthenticatedAPIRunner()
            response = api_runner.execute(
                vulnz_list.VulnzListAPIRequest(scan_id=scan_id, number_elements=number_elements, page=page))
            vulnerabilities = response['data']['scan']['vulnerabilities']['vulnerabilities']
            vulnz_list_table = []
            for vulnerability in vulnerabilities:
                vulnz_list_table.append({
                    'id': str(vulnerability['id']),
                    'risk_rating': styles.style_risk(vulnerability['detail']['riskRating'].upper()),
                    'cvss_v3_vector': vulnerability['detail']['cvssV3Vector'],
                    'title': vulnerability['detail']['title'],
                    'short_description': markdown.Markdown(vulnerability['detail']['shortDescription']),
                })
            columns = {
                'Id': 'id',
                'Title': 'title',
                'Risk Rating': 'risk_rating',
                'CVSS V3 Vector': 'cvss_v3_vector',
                'Short Description': 'short_description',
            }
            title = f'Scan {scan_id}: Found {len(vulnz_list_table)} vulnerabilities.'
            console.table(columns=columns, data=vulnz_list_table, title=title)
            has_next_page: bool = response['data']['scan']['vulnerabilities']['pageInfo']['hasNext']
            num_pages = response['data']['scan']['vulnerabilities']['pageInfo']['numPages']
            if has_next_page is True:
                console.info('Fetch next page?')
                page = page + 1
                if click.confirm(f'page {page + 1} of {num_pages}'):
                    self.list_vulnz(scan_id=scan_id, page=page, number_elements=number_elements)
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
            'Risk Rating': 'risk_rating',
            'CVSSv3 Vector': 'cvss_v3_vector',
            'Short Description': 'short_description',
        }
        title = f'Describing vulnerability {vulnerability["id"]}'
        console.table(columns=columns, data=vulnz_list_data, title=title)
        rich.print(panel.Panel(markdown.Markdown(vulnerability['detail']['description']), title='Description'))
        rich.print(panel.Panel(markdown.Markdown(vulnerability['detail']['recommendation']), title='Recommendation'))
        if vulnerability['technicalDetailFormat'] == 'HTML':
            rich.print(panel.Panel(markdown.Markdown(markdownify.markdownify(vulnerability['technicalDetail'])),
                                   title='Technical details'))
        else:
            rich.print(panel.Panel(markdown.Markdown(vulnerability['technicalDetail']), title='Technical details'))

    def describe_vuln(self, scan_id: int, vuln_id: int, page: int = 1, number_elements: int = 10):
        """Fetch and show the full details of specific vuln from the cloud, or all the vulnz for a specific scan.

        Args:
            scan_id: scan id to show all vulnerabilities.
            vuln_id: optional vuln id to describe.
            page: page number.
            number_elements: number of items to show per page.
        """
        try:
            if vuln_id is None:
                click.BadParameter('You should at least provide --vuln_id or --scan_id.')
            api_runner = authenticated_runner.AuthenticatedAPIRunner()
            if scan_id is not None:
                response = api_runner.execute(
                    vulnz_describe.ScanVulnzDescribeAPIRequest(scan_id=scan_id,
                                                               vuln_id=vuln_id,
                                                               page=page,
                                                               number_elements=number_elements))
                vulnerabilities = response['data']['scan']['vulnerabilities']['vulnerabilities']
                for v in vulnerabilities:
                    self._print_vulnerability(v)
                num_pages = response['data']['scan']['vulnerabilities']['pageInfo']['numPages']
                console.success(f'Vulnerabilities listed successfully. page {page} of {num_pages} pages')
                has_next_page: bool = response['data']['scan']['vulnerabilities']['pageInfo']['hasNext']
                if has_next_page is True:
                    console.info('Fetch next page?')
                    page = page + 1
                    if click.confirm(f'page {page + 1} of {num_pages}'):
                        self.describe_vuln(scan_id=scan_id, vuln_id=vuln_id, page=page, number_elements=number_elements)

        except runner.ResponseError:
            console.error('Vulnerability / scan not Found.')

    def _fetch_scan_vulnz(self, scan_id: int, page: int = 1, number_elements: int = 10):
        api_runner = authenticated_runner.AuthenticatedAPIRunner()
        return api_runner.execute(
            vulnz_list.VulnzListAPIRequest(scan_id=scan_id, number_elements=number_elements, page=page))

    def dump_vulnz(self, scan_id: int, dumper: dumpers.VulnzDumper, page: int = 1, number_elements: int = 10):
        """fetch vulnz from the cloud runtime.
        fetching all vulnz for a specific scan and saving in a specific format, in order to fetch all vulnerabilities
        {number_elements|10} for each request, this function run in an infinity loop (recursive)
        Args:
            dumper: VulnzDumper class
            scan_id: scan id to dump vulnz from.
            page: page number
            number_elements: number of elements per reach page
        """
        has_next_page = True
        with console.status(f'fetching vulnerabilities for scan scan-id={scan_id}'):
            while has_next_page:
                response = self._fetch_scan_vulnz(scan_id, page=page, number_elements=number_elements)
                has_next_page: bool = response['data']['scan']['vulnerabilities']['pageInfo']['hasNext'] | False
                page = page + 1
                vulnerabilities = response['data']['scan']['vulnerabilities']['vulnerabilities']
                vulnz_list_table = []
                for vulnerability in vulnerabilities:
                    vuln = {
                        'id': str(vulnerability['id']),
                        'risk_rating': vulnerability['detail']['riskRating'],
                        'cvss_v3_vector': vulnerability['detail']['cvssV3Vector'],
                        'title': vulnerability['detail']['title'],
                        'short_description': vulnerability['detail']['shortDescription'],
                        'description': vulnerability['detail']['description'],
                        'recommendation': vulnerability['detail']['recommendation'],
                        'technical_detail': vulnerability['technicalDetail'],
                    }
                    vulnz_list_table.append(vuln)
                dumper.dump(vulnz_list_table)
                console.success(f'{len(vulnerabilities)} Vulnerabilities saved to {dumper.output_path}')

    def _check_agents_exist(self, agent_group_definition: definitions.AgentGroupDefinition) -> bool:
        """Send API requests to check if agents exist."""
        api_runner = authenticated_runner.AuthenticatedAPIRunner()

        for agent in agent_group_definition.agents:
            response = api_runner.execute(agent_details.AgentDetailsAPIRequest(agent.key))
            if response.get('errors') is not None:
                console.errors('The agent {agent.key} does not exists')
                return False
        return True

    def _agents_from_agent_group_def(self,
                                     api_runner: runner.APIRunner,
                                     agent_group_definition: definitions.AgentGroupDefinition) -> List[AgentType]:
        """Creates list of agents dicts from an agent group definition."""
        agents = []
        for agent_def in agent_group_definition.agents:
            agent_detail = api_runner.execute(agent_details.AgentDetailsAPIRequest(agent_def.key))
            agent_version = agent_detail['data']['agent']['versions']['versions'][0]['version']
            agent = {}
            agent['agentKey'] = agent_def.key
            agent['version'] = agent_version

            agent_args = []
            for arg in agent_def.args:
                agent_args.append({
                    'name': arg.name,
                    'type': arg.type,
                    'value': arg.value
                })
            agent['args'] = agent_args
            agents.append(agent)
        return agents

    def _create_agent_group(self, api_runner: runner.APIRunner, name: str, description: str, agents: List[AgentType]):
        """Sends an API request to create an agent group.

        Returns:
            id opf the created agent group.
        """
        request = agent_group.CreateAgentGroupAPIRequest(name, description, agents)
        response = api_runner.execute(request)
        agent_group_id = response['data']['publishAgentGroup']['agentGroup']['id']
        return agent_group_id

    def _create_asset(self, api_runner: runner.APIRunner, asset: base_asset.Asset):
        """Sends an API request to create an asset.

        Returns:
            id of the created asset.
        """
        request = api_assets.CreateAssetAPIRequest(asset)
        response = api_runner.execute(request)
        asset_id = response['data']['createAsset']['asset']['id']
        return asset_id

    def _create_scan(self, api_runner: runner.APIRunner, asset_id: int, agent_group_id: int, title: str):
        """Sends an API request to create a scan."""
        request = create_agent_scan.CreateAgentScanAPIRequest(title, asset_id, agent_group_id)
        _ = api_runner.execute(request)
