"""Auth logout command."""

from ostorlab import configuration_manager
from ostorlab.cli import console as cli_console
from ostorlab.cli.auth import auth

console = cli_console.Console()


@auth.auth.command()
def logout() -> None:
    """Use this to log out locally by deleting the stored authorization token."""
    configuration_manager.ConfigurationManager().delete_authorization_token_data()
    console.success("You successfully logged out")
