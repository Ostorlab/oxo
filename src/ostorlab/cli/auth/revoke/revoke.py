"""Auth revoke command."""

import logging

from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis.runners import runner
from ostorlab.apis import logout as logout_api
from ostorlab import configuration_manager
from ostorlab.cli.auth import auth
from ostorlab.cli import console as cli_console

logger = logging.getLogger(__name__)
console = cli_console.Console()


@auth.auth.command()
def revoke():
    """Use this to log out."""
    config_manager = configuration_manager.ConfigurationManager()

    authorization_token = config_manager.authorization_token
    api_runner = authenticated_runner.AuthenticatedAPIRunner()

    with console.status("Loging out"):
        try:
            if authorization_token is not None:
                api_runner.execute(logout_api.LogoutAPIRequest())
            api_runner.unauthenticate()
            config_manager.delete_authorization_token_data()
            console.success("You successfully log out")
        except runner.ResponseError:
            console.error(
                "Error response. The reason could be the authorization token is invalid."
            )
            api_runner.unauthenticate()
