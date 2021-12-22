import click
from ostorlab.runtimes import LocalRuntime
from ostorlab.runtimes.runtime import AgentRunDefinition


@click.group()
@click.option('--proxy', '-X', help='Proxy to route HTTPS requests through.')
@click.option("--tlsverify/--no-tlsverify", default=True)
@click.pass_context
def rootcli(ctx, proxy, tlsverify):
    ctx.obj = {
        'proxy': proxy,
        'tlsverify': tlsverify
    }
    pass


@rootcli.group()
@click.option('--runtime', type=click.Choice(['local', 'managed', 'hybrid']), help='run time ', required=True)
@click.option('--agents', multiple=True, help='run time ', required=True)
@click.option('--title', '-t', help='Scan title.')
@click.option('--agents-group', type=click.File('r'), help='agents-group ')
@click.pass_context
def scan(ctx, runtime, agents, agents_group, title):
    """ Start a new scan """

    if runtime == 'local':
        runtime = LocalRuntime()
    else:
        raise NotImplementedError()

    agent_run_definition = AgentRunDefinition(agent_groups=agents_group, agents=agents)
    if runtime.can_run(agent_run_definition=agent_run_definition):
        ctx.obj['runtime'] = runtime
        ctx.obj['agent_run_definition'] = agent_run_definition
        ctx.obj['title'] = title
    else:
        raise click.ClickException('can use the provided agents list')


@rootcli.group()
def agent():
    raise NotImplementedError()
    pass


@rootcli.group()
def agentgroup():
    raise NotImplementedError()
    pass
