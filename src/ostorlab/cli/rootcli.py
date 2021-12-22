""" root cli for ostorlab cli"""
import io
from typing import List, Optional
import click
from ostorlab.runtimes import LocalRuntime, AgentBuilder, AgentGroupBuilder
from ostorlab.runtimes.runtime import AgentRunDefinition, AgentGroupDefinition, AgentDefinition


@click.group()
@click.option('--proxy', '-X', help='Proxy to route HTTPS requests through.')
@click.option("--tlsverify/--no-tlsverify", default=True)
@click.pass_context
def rootcli(ctx: click.core.Context, proxy: Optional[str], tlsverify: bool) -> None:
    """
    root command for ostorlab cli initiate the context, Available commands
    - scan
    - agent
    - agent-group

    Args:
        ctx (click.core.Context): click Context object
        proxy (Optional[str]): Proxy to route HTTPS requests through.
        tlsverify (bool): Enabled/Disable tlsverify

    Returns:
        None
    """

    ctx.obj = {
        'proxy': proxy,
        'tlsverify': tlsverify
    }


@rootcli.group()
@click.option('--runtime', type=click.Choice(['local', 'managed', 'hybrid']), help='run time ', required=True)
@click.option('--agents', multiple=True, help='list of Agents ', required=True)
@click.option('--title', '-t', help='Scan title.')
@click.option('--agents-group-definition', '-agd', type=click.File('r'), help='agents-group.yaml file', multiple=True)
@click.pass_context
def scan(ctx: click.core.Context, runtime: str, agents: List[str], agents_group_definition: List[io.FileIO],
         title: str) -> None:
    """ Start a new scan on a provided asset

    Args:
        ctx (click.core.Context): click Context object
        runtime (str): specify the runtime type ['local', 'managed', 'hybrid']
        agents (List[str]): List of agents names to use in the scan
        agents_group_definition ( List[io.FileIO]): List of agents_group_definition .yaml files
        title (str): title for scan

    Returns:
        None: 
        Raises:
            - AgentDefinitionError : when one or multiple agent definition is not valid
    """

    if runtime == 'local':
        runtime = LocalRuntime()
    else:
        # managed and hybrid are not implemented
        raise NotImplementedError()

    # Building List of Agents definition
    agents_definition: List[AgentDefinition] = []
    for agent_key in agents:
        agents_definition.append(AgentBuilder().build(agent_key=agent_key))

    # Building List of Agents definition
    agents_groups: List[AgentGroupDefinition] = []
    for group in agents_group_definition:
        agents_groups.append(AgentGroupBuilder().build(group))

    agent_run_definition = AgentRunDefinition(agent_groups=agents_groups, agents=agents_definition)
    if runtime.can_run(agent_run_definition=agent_run_definition):
        ctx.obj['runtime'] = runtime
        ctx.obj['agent_run_definition'] = agent_run_definition
        ctx.obj['title'] = title
    else:
        raise click.ClickException('can use the provided agents/ agent group list  ')


@rootcli.group()
def agent():
    raise NotImplementedError()


@rootcli.group()
def agentgroup():
    raise NotImplementedError()
