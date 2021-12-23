"""Entry point for ostorlab cli. with the main commands."""
import io
import click
from typing import List, Optional
from ostorlab import runtimes


@click.group()
@click.option('--proxy', '-X', help='Proxy to route HTTPS requests through.')
@click.option('--tlsverify/--no-tlsverify', default=True)
@click.pass_context
def rootcli(ctx: click.core.Context, proxy: Optional[str], tlsverify: bool) -> None:
    """ostorlab cli. Open source tool to AUTOMATE YOUR SECURITY TESTING."""

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
    """scan command: Start a new scan on a provided asset.\n
    usage:\n
        - ostorlab scan --agents=agent1,agent2 --title=test_scan
    """

    if runtime == 'local':
        runtime = runtimes.LocalRuntime()
    else:
        # managed and hybrid are not implemented
        raise NotImplementedError()

    # Building list of agents definition
    agents_definition: List[runtimes.AgentDefinition] = []
    for agent_key in agents:
        agents_definition.append(runtimes.AgentDefinition.from_agent_key(agent_key=agent_key))

    # Building list of agent group definition
    agents_groups: List[runtimes.AgentGroupDefinition] = []
    for group in agents_group_definition:
        agents_groups.append(runtimes.AgentGroupDefinition.from_file(group))

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
