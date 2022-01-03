"""Module for the command run inside the group scan.
This module takes care of preparing the selected runtime and the lists of provided agents, before starting a scan.
Example of usage:
    - ostorlab scan run --agents=agent1,agent2 --title=test_scan [asset] [options]."""
import io
from typing import List
import click
from ostorlab import runtimes
from ostorlab.runtimes import definitions
from ostorlab.cli.scan import scan


@scan.group()
@click.option('--runtime', type=click.Choice(['local', 'managed', 'hybrid']),
              help="""Runtime is in charge of preparing the environment to trigger a scan.\n
                    Specify which runtime to use: \n
                    local: on you local machine \n
                    managed: on Ostorlab cloud, (requires login) \n
                    hybrid: soon!. \n
                   """,
              required=True)
@click.option('--agents', multiple=True, help='List of agents keys. to use in the scan. ', required=True)
@click.option('--title', '-t', help='Scan title.')
@click.option('--agents-group-definition', '-g', type=click.File('r'),
              help='Path to agents group definition file (yaml).', multiple=True)
@click.pass_context
def run(ctx: click.core.Context, runtime: str, agents: List[str], agents_group_definition: List[io.FileIO],
        title: str) -> None:
    """Start a new scan on a specific asset.\n
    Usage:\n
        - ostorlab scan run --agents=agent1,agent2 --title=test_scan android-apk --file=path/to/application.apk
    """

    if runtime == 'local':
        runtime = runtimes.LocalRuntime()
    else:
        # managed and hybrid are not implemented yet
        raise click.ClickException(f'The selected runtime {runtime} is not supported!')

    # Building list of agents definition
    agents_settings: List[definitions.AgentSettings] = []
    for agent_key in agents:
        agents_settings.append(
            definitions.AgentSettings(key=agent_key))

    # Building list of agent group definition
    agents_groups: List[definitions.AgentGroupDefinition] = []
    for group in agents_group_definition:
        agents_groups.append(definitions.AgentGroupDefinition.from_file(group))

    agent_run_definition = definitions.AgentRunDefinition(
        agent_groups=agents_groups, agents=agents_settings)
    if runtime.can_run(agent_group_definition=agent_run_definition):
        ctx.obj['runtime'] = runtime
        ctx.obj['agent_run_definition'] = agent_run_definition
        ctx.obj['title'] = title
    else:
        raise click.ClickException('Error: invalid agent list.')
