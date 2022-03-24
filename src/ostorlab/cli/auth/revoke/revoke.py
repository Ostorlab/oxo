"""Auth revoke command."""

import logging

from ostorlab.apis.runners import authenticated_runner
from ostorlab.apis.runners import runner
from ostorlab.apis import revoke_api_key
from ostorlab import configuration_manager
from ostorlab.cli.auth import auth
from ostorlab.cli import console as cli_console

logger = logging.getLogger(__name__)
console = cli_console.Console()


@auth.auth.command()
def revoke():
    """Use this to revoke your API key."""

    config_manager = configuration_manager.ConfigurationManager()

    try:
        api_key_id = config_manager.api_key_id
        api_runner = authenticated_runner.AuthenticatedAPIRunner()

        with console.status('Revoking API key'):
            try:
                api_runner.execute(revoke_api_key.RevokeAPIKeyAPIRequest(api_key_id))
                api_runner.unauthenticate()
                config_manager.delete_api_data()
                console.success('API key revoked')
            except runner.ResponseError:
                console.error('Could not revoke your API key.')

    except authenticated_runner.AuthenticationError:
        api_runner.unauthenticate()
        console.success('Your API key has already been revoked.')
