""" Entry point for ostorlab cli. with the main commands. """
import io
import click
from typing import List, Optional
from ostorlab import runtimes


@click.group()
@click.option('--proxy', '-X', help='Proxy to route HTTPS requests through.')
@click.option('--tlsverify/--no-tlsverify', default=True)
@click.pass_context
def rootcli(ctx: click.core.Context, proxy: Optional[str], tlsverify: bool) -> None:
    """
    root command for ostorlab cli initiate the context
    Args:
        ctx (click.core.Context): click context object
        proxy (Optional[str]): proxy to route HTTPS requests through.
        tlsverify (bool): enabled/disable tlsverify

    Returns:
        None
    """

    ctx.obj = {
        'proxy': proxy,
        'tlsverify': tlsverify
    }


@rootcli.group()
@click.option('--runtime', type=click.Choice(['local', 'managed', 'hybrid']),
              help="""
                    specify the runtime to use: \n
                    local: on you local machine \n
                    managed: on Ostorlab cloud, (requires login) \n
                    hybrid: soon!. \n
                   """,
              required=True)
@click.option('--agents', multiple=True, help='List of agents keys. to use in the scan. ', required=True)
@click.option('--title', '-t', help='Scan title.')
@click.option('--agents-group-definition', '-agd', type=click.File('r'),
              help='path to agents group definition file (yaml).', multiple=True)
@click.pass_context
def scan(ctx: click.core.Context, runtime: str, agents: List[str], agents_group_definition: List[io.FileIO],
         title: str) -> None:
    """ Start a new scan on a provided asset

    Args:
        ctx (click.core.Context): click Context object
        runtime (str): specify the runtime type ['local', 'managed', 'hybrid']
        agents (List[str]): List of agents names to use in the scan
        agents_group_definition ( List[io.FileIO]): List of agents group definition .yaml files
        title (str): title for scan

    Returns:
        None
        Raises:
            - AgentDefinitionError : when one or multiple agent definition is not valid
    """

    if runtime == 'local':
        runtime = runtimes.LocalRuntime()
    else:
        # managed and hybrid are not implemented
        raise NotImplementedError()

    # Building List of Agents definition
    agents_definition: List[runtimes.AgentDefinition] = []
    for agent_key in agents:
        agents_definition.append(runtimes.AgentDefinition.from_agent_key(agent_key=agent_key))

    # Building List of Agents definition
    agents_groups: List[runtimes.AgentGroupDefinition] = []
    for group in agents_group_definition:
        agents_groups.append(runtimes.AgentGroupDefinition.from_file(group))

    #
    agent_run_definition = runtimes.AgentRunDefinition(agent_groups=agents_groups, agents=agents_definition)
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
