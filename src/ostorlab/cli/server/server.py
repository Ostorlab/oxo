"""Module for the ostorlab server run command."""

from ostorlab.cli.rootcli import rootcli


@rootcli.group()
def server() -> None:
    """Run the flask server."""
    pass
