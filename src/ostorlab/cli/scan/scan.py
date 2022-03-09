"""Scan module that handles running a scan using a list of agent keys and a target asset."""

from typing import Optional

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
@click.option('--bus-url', help='Bus URL, this flag is restricted to the lite local runtime.', required=False)
@click.option('--bus-vhost', help='Bus vhost, this flag is restricted to the lite local runtime.', required=False)
@click.option('--bus-management-url', help='Bus management URL, this flag is restricted to the lite local runtime.',
              required=False)
@click.option('--bus-exchange-topic', help='Bus exchange topic, this flag is restricted to the lite local runtime.',
              required=False)
@click.option('--scan-id', help='Scan id, this flag is restricted to the lite local runtime..', required=False)
@click.pass_context
def scan(ctx: click.core.Context, runtime: str,
         bus_url: Optional[str] = None,
         bus_vhost: Optional[str] = None,
         bus_management_url: Optional[str] = None,
         bus_exchange_topic: Optional[str] = None,
         scan_id: Optional[str] = None
         ) -> None:
    """You can use scan [subcommand] to list, start or stop a scan.\n
    Examples:\n
        - Show list of scans: ostorlab scan --list\n
        - Show full details of a scan: ostorlab scan describe --scan=scan_id.\n
    """
    try:
        runtime_instance = registry.select_runtime(runtime,
                                                   scan_id=scan_id,
                                                   bus_url=bus_url,
                                                   bus_vhost=bus_vhost,
                                                   bus_management_url=bus_management_url,
                                                   bus_exchange_topic=bus_exchange_topic
                                                   )
        ctx.obj['runtime'] = runtime_instance
    except registry.RuntimeNotFoundError as e:
        raise click.ClickException(f'The selected runtime {runtime} is not supported.') from e
    except ValueError as e:
        raise click.ClickException(f'Error initializing runtime {runtime}.') from e
