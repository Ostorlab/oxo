import logging
"""Python's module which implements a flexible event logging system. Documentation: https://docs.python.org/3/library/logging.html
"""

import click
"""Package for creating beautiful command line interfaces in a composable way. Documentation: https://click.palletsprojects.com/en/8.0.x/
"""

from ostorlab.apis import runner as apis_runner
"""the APIRunner that handles all API calls
"""

from ostorlab.cli.rootcli import auth
"""the auth group that allows us to use the auth command and it's subcommands
"""

logger = logging.getLogger(__name__)

@auth.command()
@click.option('--username', '-u', help='Ostorlab platform username.', required=True)
@click.option('--password', '-p', help='Ostorlab platform password.', required=True)
@click.option('--token-duration', help='Expiration time for token (m for minutes, h for hours, and d for days).')
def login(username, password, token_duration):
    """Gets the login credentials from the user and calls the APIRunner

    Args:
        username: the username (email) used to login
        password: the password used to login
        token_duration: The duration for which the token is valid (Can be in minutes, hours, days, or a combination of any two or all three)
    """    
    try:
        api_runner = apis_runner.APIRunner(username=username, password=password,
                                           token_duration=token_duration)
        api_runner.authenticate()
    except apis_runner.AuthenticationError:
        logger.error(
            'Authentication error, please check that your credentials are valid.')
