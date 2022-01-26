"""Scan module that handles running a scan using a list of agent keys and a target asset."""

import click

from ostorlab.cli.rootcli import rootcli
from ostorlab.runtimes import registry


@rootcli.group()
@click.option('--runtime', type=click.Choice(['local', 'remote', 'hybrid']),
              help="""Runtime is in charge of preparing the environment to trigger a scan.\n
                    Specify which runtime to use: \n
                    local: on you local machine\n
                    remote: on Ostorlab cloud, (requires login)\n
                    hybrid: running partially on Ostorlab cloud and partially on the local machine\n
                   """,
              default='local',
              required=True)
@click.pass_context
def scan(ctx: click.core.Context, runtime: str) -> None:
    """You can use scan [subcommand] to list, start or stop a scan.\n
    Examples:\n
        - Show list of scans: ostorlab scan --list\n
        - Show full details of a scan: ostorlab scan describe --scan=scan_id.\n
    """
    try:
        runtime_instance = registry.select_runtime(runtime)
        ctx.obj['runtime'] = runtime_instance
    except registry.RuntimeNotFoundError as e:
        raise click.ClickException(f'The selected runtime {runtime} is not supported.') from e
