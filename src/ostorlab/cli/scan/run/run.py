"""Module for the command run inside the group scan.
This module takes care of preparing the selected runtime and the lists of provided agents, before starting a scan.
Example of usage:
    - ostorlab scan run --agents=agent1,agent2 --title=test_scan [asset] [options]."""
import io
from typing import List
import click
from ostorlab.runtimes import definitions
from ostorlab.cli.scan import scan


@scan.group()
@click.option('--agents', multiple=True, help='List of agents keys. to use in the scan. ', required=True)
@click.option('--title', '-t', help='Scan title.')
@click.option('--agent-group-definition', '-g', type=click.File('r'),
              help='Path to agents group definition file (yaml).')
@click.pass_context
def run(ctx: click.core.Context, agents: List[str], agent_group_definition: io.FileIO,
        title: str) -> None:
    """Start a new scan on a specific asset.\n
    Usage:\n
        - ostorlab scan run --agents=agent1,agent2 --title=test_scan android-apk --file=path/to/application.apk
    """
    if agents:
        agents_settings: List[definitions.AgentSettings] = []
        for agent_key in agents:
            agents_settings.append(
                definitions.AgentSettings(key=agent_key))
        agent_group = definitions.AgentGroupDefinition(agents=agents_settings)
    elif agent_group_definition:
        agent_group = definitions.AgentGroupDefinition.from_yaml(agent_group_definition)
    else:
        raise click.ClickException('Missing agent list or agent group definition.')

    runtime_instance = ctx.obj['runtime']
    if runtime_instance.can_run(agent_group_definition=agent_group):
        ctx.obj['agent_group_definition'] = agent_group
        ctx.obj['title'] = title
    else:
        raise click.ClickException('Runtime do not support provided agent list or group definition.')
