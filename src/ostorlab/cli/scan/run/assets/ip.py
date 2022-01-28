"""Asset of type file.
This module takes care of preparing a generic file of type before injecting it to the runtime instance."""
import logging
import ipaddress
import click
from ostorlab.cli import console as cli_console
from ostorlab.assets import ipv4
from ostorlab.assets import ipv6
from ostorlab.cli.scan.run import run

logger = logging.getLogger(__name__)

console = cli_console.Console()

@run.run.command(name='ip')
@click.argument('ip', required=True)
@click.pass_context
def ip_cli(ctx: click.core.Context, ip: str) -> None:
    """Run scan for IP asset."""
    runtime = ctx.obj['runtime']
    try:
        ip_network = ipaddress.ip_network(ip, strict=False)
        if ip_network.version == 4:
            asset = ipv4.IPv4(host=ip_network.network_address.exploded, mask=ip_network.prefixlen)
        elif ip_network.version == 6:
            asset = ipv6.IPv6(host=ip_network.network_address.exploded, mask=ip_network.prefixlen)
        else:
            raise NotImplementedError()

        logger.debug('scanning asset IP %s', asset)
        runtime.scan(agent_group_definition=ctx.obj['agent_group_definition'], asset=asset)
    except ValueError as e:
        console.error(f'{e}')
        click.Abort()
