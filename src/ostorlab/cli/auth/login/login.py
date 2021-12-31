"""Auth login command."""

import logging

import click

from ostorlab.apis import runner as apis_runner
from ostorlab.cli.auth import auth

logger = logging.getLogger(__name__)


@auth.auth.command()
@click.option('--username', '-u', help='Ostorlab platform username.', required=True)
@click.option('--password', '-p', help='Ostorlab platform password.', required=True)
@click.option('--token-duration', help='Expiration time for token (m for minutes, h for hours, and d for days).')
def login(username, password, token_duration):
    """Use this to log into your account."""
    try:
        api_runner = apis_runner.APIRunner(username=username, password=password,
                                           token_duration=token_duration)
        api_runner.authenticate()
    except apis_runner.AuthenticationError:
        logger.error(
            'Authentication error, please check that your credentials are valid.')
