"""Vulnz module that handles listing and describing a vulnerability."""
import click

from ostorlab.cli.rootcli import rootcli
from ostorlab.runtimes import registry


@rootcli.group()
@click.option('--runtime', type=click.Choice(['local', 'litelocal', 'cloud', 'hybrid']),
              help="""Runtime is in charge of preparing the environment to trigger a scan.\n
                    Specify which runtime to use: \n
                    local: on you local machine\n
                    litelocal: stripped down local runtime\n
                    cloud: on Ostorlab cloud, (requires login)\n
                    hybrid: running partially on Ostorlab cloud and partially on the local machine\n
                   """,
              default='local',
              required=True)
@click.pass_context
def vulnz(ctx, runtime: str = 'local') -> None:
    """You can use vulnz to list and describe vulnerabilities.\n"""
    try:
        runtime_instance = registry.select_runtime(runtime_type=runtime)
        ctx.obj['runtime'] = runtime_instance
    except registry.RuntimeNotFoundError as e:
        raise click.ClickException(f'The selected runtime {runtime} is not supported.') from e
    pass
