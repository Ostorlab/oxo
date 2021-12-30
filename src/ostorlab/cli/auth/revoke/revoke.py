"""Auth revoke command."""

import logging

from ostorlab.apis import runner as apis_runner
from ostorlab.cli.auth import auth

logger = logging.getLogger(__name__)


@auth.auth.command()
def revoke():
    """Use this to revoke your API key.
    """
    try:
        apis_runner.APIRunner().revoke_api_key()
    except apis_runner.AuthenticationError:
        logger.error(
            'Error, OrganizationAPIKey matching query does not exist.')
