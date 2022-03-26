"""Agent search command."""
import logging
from typing import Dict

import click
from rich import markdown

from ostorlab import configuration_manager
from ostorlab.apis import agent_search as agent_search_api
from ostorlab.apis.runners import public_runner, authenticated_runner
from ostorlab.apis.runners import runner as base_runner
from ostorlab.cli import console as cli_console
from ostorlab.cli.agent import agent

console = cli_console.Console()

logger = logging.getLogger(__name__)


@agent.command(name='search')
@click.option('--keyword', '-k', help='Keyword to use for the search.', required=True)
def search_cli(keyword: str) -> None:
    """CLI command to search for agents in the Agents store."""
    result_agents = search_agents(keyword).get('agents')
    console.success('Search agents done.')
    agents = []
    version = ''
    description = ''
    in_selectors = ''
    out_selectors = ''

    if result_agents is not None:
        for result_agent in result_agents:
            versions = result_agent['versions'].get('versions')
            if len(versions) > 0:
                version = versions[0].get('version')
                description = versions[0].get('description')
                in_selectors = ', '.join(versions[0].get('inSelectors'))
                out_selectors = ','.join(versions[0].get('outSelectors'))
            else:
                version = '-'
                description = '-'
                in_selectors = '-'
                out_selectors = '-'

            agents.append({
                'key': result_agent['key'],
                'version': version,
                'description': markdown.Markdown(description),
                'in_selectors': in_selectors,
                'out_selectors': out_selectors
            })

    columns = {
        'Agent key': 'key',
        'Version': 'version',
        'Description': 'description',
        'In selectors': 'in_selectors',
        'Out selectors': 'out_selectors',
    }
    title = f'Found {len(agents)} Agents'
    console.table(columns=columns, data=agents, title=title)


def search_agents(search: str) -> Dict:
    """Sends an API request with the agent key, and retrieve the agent information.

    Args:
        search: the keyword to search for

    Returns:
        List of agent matching the search.

    Raises:
        click Exit exception with satus code 2 when API response is invalid.
    """
    config_manager = configuration_manager.ConfigurationManager()

    if config_manager.is_authenticated:
        runner = authenticated_runner.AuthenticatedAPIRunner()
    else:
        runner = public_runner.PublicAPIRunner()

    try:
        response = runner.execute(agent_search_api.AgentSearchAPIRequest(search))
    except base_runner.ResponseError as e:
        console.error('Requested resource not found.')
        raise click.exceptions.Exit(2) from e

    if 'errors' in response:
        error_message = f'The provided search : {search} does not correspond to any agent.'
        console.error(error_message)
        raise click.exceptions.Exit(2)
    else:
        agent_details = response['data']['agents']
        return agent_details
