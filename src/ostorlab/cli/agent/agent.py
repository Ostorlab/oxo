"""Agent module that handles building, searching, installing, bootstraping and running an agent."""

from ostorlab.cli.rootcli import rootcli


@rootcli.group()
def agent() -> None:
    """You can use agent to search, install, bootstrap and run an agent.\n"""
    pass
