"""Auth module that handles login."""

from ostorlab.cli.rootcli import rootcli

@rootcli.group()
def auth() -> None:
    """You can use 'auth [subcommand] [options]' to authenticate."""
    pass
