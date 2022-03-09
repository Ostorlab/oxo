"""Module for the command run inside the group scan.
This module takes care of preparing the selected runtime and the lists of provided agents, before starting a scan.
Example of usage:
    - ostorlab scan run --agent=agent1 --agent=agent2 --title=test_scan [asset] [options]."""
import io
import logging
from typing import List

import click

from ostorlab.cli import install_agent
from ostorlab.cli.scan import scan
from ostorlab.runtimes import definitions
from ostorlab.runtimes import runtime
from ostorlab.cli import console as cli_console

console = cli_console.Console()

logger = logging.getLogger(__name__)

@scan.group()
@click.option('--agent',
              multiple=True,
              help='List of agents keys. to use in the scan.',
              required=False)
@click.option('--title', '-t', help='Scan title.')
@click.option('--agent-group-definition', '-g', type=click.File('r'),
              help='Path to agents group definition file (yaml).',
              required=False)
@click.option('--install', '-i', help='Install missing agents.', is_flag=True, required=False)
@click.option('--follow', help='Follow logs of provided list of agents and services.', multiple=True, default=[])
@click.pass_context
def run(ctx: click.core.Context, agent: List[str], agent_group_definition: io.FileIO,
        title: str, install: bool, follow: List[str]) -> None:
    """Start a new scan on a specific asset.\n
    Example:\n
        - ostorlab scan run --agents=agent/ostorlab/nmap,agent/google/tsunami --title=test_scan ip 8.8.8.8
    """
    if agent:
        agents_settings: List[definitions.AgentSettings] = []
        for agent_key in agent:
            agents_settings.append(
                definitions.AgentSettings(key=agent_key))

        agent_group = definitions.AgentGroupDefinition(agents=agents_settings)
    elif agent_group_definition:
        agent_group = definitions.AgentGroupDefinition.from_yaml(agent_group_definition)
    else:
        raise click.ClickException('Missing agent list or agent group definition.')

    runtime_instance: runtime.Runtime = ctx.obj['runtime']
    # set list of log follow.
    runtime_instance.follow = follow

    if runtime_instance.can_run(agent_group_definition=agent_group):
        ctx.obj['agent_group_definition'] = agent_group
        ctx.obj['title'] = title

        if install:
            # Trigger both the runtime installation routine and install all the provided agents.
            runtime_instance.install()
            for ag in agent_group.agents:
                try:
                    install_agent.install(ag.key)
                except install_agent.AgentDetailsNotFound:
                    console.warning(f'agent {ag.key} not found on the store')
    else:
        raise click.ClickException('The runtime does not support the provided agent list or group definition.')
