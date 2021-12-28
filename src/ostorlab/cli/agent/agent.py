"""Agent module that handles building, searching, installing, bootstraping and running an agent."""
from ostorlab.cli.rootcli import rootcli
import click


@rootcli.group()
@click.pass_context
def agent(ctx: click.core.Context) -> None:
    """You can use agent to search, install, bootstrap and run an agent.\n"""
    pass
