"""Scan module that handles running a scan using a list of agent keys and a target asset."""
from ostorlab.cli.rootcli import rootcli
import click


@rootcli.group()
@click.pass_context
def scan(ctx: click.core.Context) -> None:
    """You can use scan [subcommand] to list, start or stop a scan.\n
    Examples:\n
        - Show list of scans: ostorlab scan --list\n
        - show full details of a scan: ostorlab scan describe --scan=scan_id.\n
    """
    pass



