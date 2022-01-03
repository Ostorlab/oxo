"""Auth revoke command."""

import logging

from ostorlab.apis import runner as apis_runner
from ostorlab.apis import revoke_api_key
from ostorlab import configuration_manager
from ostorlab.cli.auth import auth

logger = logging.getLogger(__name__)


@auth.auth.command()
def revoke():
    """Use this to revoke your API key.
    """
    config_manager = configuration_manager.ConfigurationManager()

    try:
        api_key_id = config_manager.get_api_key_id()
        runner = apis_runner.APIRunner()

        response = runner.execute(revoke_api_key.RevokeAPIKeyAPIRequest(api_key_id))
        if response.get('errors') is not None:
            logger.error('Error revoking your API key.')


        runner.unauthenticate()
        config_manager.delete_api_data()
    except apis_runner.AuthenticationError:
        runner.unauthenticate()
        logger.error('Your API key has already been revoked.')
