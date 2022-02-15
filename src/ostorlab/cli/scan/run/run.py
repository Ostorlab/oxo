"""Module for the command run inside the group scan.
This module takes care of preparing the selected runtime and the lists of provided agents, before starting a scan.
Example of usage:
    - ostorlab scan run --agents=agent1,agent2 --title=test_scan [asset] [options]."""
import io
from typing import List

import click

from ostorlab.cli import install_agent
from ostorlab.cli.scan import scan
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime


@scan.group()
@click.option('--agents',
              multiple=True,
              help='List of agents keys. to use in the scan. ',
              required=False)
@click.option('--title', '-t', help='Scan title.')
@click.option('--agent-group-definition', '-g', type=click.File('r'),
              help='Path to agents group definition file (yaml).',
              required=False)
@click.option('--install', '-i', help='Install missing agents', is_flag=True, required=False)
@click.pass_context
def run(ctx: click.core.Context, agents: List[str], agent_group_definition: io.FileIO,
        title: str, install: bool) -> None:
    """Start a new scan on a specific asset.\n
    Example:\n
        - ostorlab scan run --agents=agent/ostorlab/nmap,agent/google/tsunami --title=test_scan ip 8.8.8.8
    """
    if agents:
        agents_settings: List[definitions.AgentSettings] = []
        for agent_key in agents:
            agents_settings.append(
                definitions.AgentSettings(key=agent_key))
            if install:
                install_agent.install(agent_key)
        agent_group = definitions.AgentGroupDefinition(agents=agents_settings)
    elif agent_group_definition:
        agent_group = definitions.AgentGroupDefinition.from_yaml(agent_group_definition)
    else:
        raise click.ClickException('Missing agent list or agent group definition.')

    runtime_instance: runtime.Runtime = ctx.obj['runtime']
    if runtime_instance.can_run(agent_group_definition=agent_group):
        ctx.obj['agent_group_definition'] = agent_group
        ctx.obj['title'] = title

        if install:
            # Trigger both the runtime installation routine and install all the provided agents.
            runtime_instance.install()
            for agent in agent_group.agents:
                install_agent.install(agent.key)
    else:
        raise click.ClickException('The runtime does not support the provided agent list or group definition.')
