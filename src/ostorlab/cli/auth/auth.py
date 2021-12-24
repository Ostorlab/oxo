"""Gets the login credentials from the user and calls the APIRunner.

This module contains logic for the auth command and it's options
(username, password, and token-duration).

  Typical usage examples:

  ostorlab auth login: authenticates the user using the persisted token if it exists,
  else, shows an error.
  ostorlab auth login -u [your_username] -p [your_password]: authenticates the user
  using the username and password.
  ostorlab auth login -u [your_username] -p [your_password] --token-duration=[desired_duration]:
  authenticates the user using the username and password, and sets the duration for which the
  token is valid.
"""

import logging

import click

from ostorlab.apis import runner as apis_runner
from ostorlab.cli.rootcli import auth

logger = logging.getLogger(__name__)


@auth.command()
@click.option('--username', '-u', help='Ostorlab platform username.', required=True)
@click.option('--password', '-p', help='Ostorlab platform password.', required=True)
@click.option('--token-duration', help='Expiration time for token (m for minutes, h for hours, and d for days).')
def login(username, password, token_duration):
    """Use this to log into your account.
    """
    try:
        api_runner = apis_runner.APIRunner(username=username, password=password,
                                           token_duration=token_duration)
        api_runner.authenticate()
    except apis_runner.AuthenticationError:
        logger.error(
            'Authentication error, please check that your credentials are valid.')

        # TODO(rabson): add fetch API key and persist API key.
