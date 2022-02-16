"""Agent List command."""
import logging

import docker

from ostorlab.cli import console as cli_console
from ostorlab.cli.agent import agent

console = cli_console.Console()

logger = logging.getLogger(__name__)


def _human_readable_size(size, decimal_places=3):
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f'{size:.{decimal_places}f}{unit}'


@agent.command(name='list')
def list_cli() -> None:
    """CLI command to list installed agents."""
    docker_client = docker.from_env()
    images = docker_client.images.list()
    console.success('Agents listed successfully.')
    agents = []
    for im in images:
        for t in im.tags:
            if t.startswith('agent_'):
                agents.append({
                    'id': im.short_id,
                    'agent': t.replace('_', '/', 2).split(':')[0],
                    'version': t.split(':')[1],
                    'size': _human_readable_size(im.attrs['Size']),
                    'created': im.attrs['Created']
                })

    columns = {
        'Agent': 'agent',
        'Version': 'version',
        'Id': 'id',
        'Size': 'size',
        'Created': 'created',
    }
    title = f'Found {len(agents)} Agents'
    console.table(columns=columns, data=agents, title=title)
