"""Scan module that handles running a scan using a list of agent keys and a target asset."""

import click

from ostorlab.cli.rootcli import rootcli
from ostorlab.runtimes import runtime as base_runtime


@rootcli.group()
@click.option('--runtime', type=click.Choice(['local', 'managed', 'hybrid']),
              help="""Runtime is in charge of preparing the environment to trigger a scan.\n
                    Specify which runtime to use: \n
                    local: on you local machine \n
                    managed: on Ostorlab cloud, (requires login) \n
                    hybrid: soon!. \n
                   """,
              required=True)
@click.pass_context
def scan(ctx: click.core.Context, runtime: str) -> None:
    """You can use scan [subcommand] to list, start or stop a scan.\n
    Examples:\n
        - Show list of scans: ostorlab scan --list\n
        - Show full details of a scan: ostorlab scan describe --scan=scan_id.\n
    """
    try:
        runtime_instance = base_runtime.Runtime.create(runtime)
        ctx.obj['runtime'] = runtime_instance
    except base_runtime.RuntimeNotFoundError as e:
        raise click.ClickException(f'The selected runtime {runtime} is not supported.') from e
