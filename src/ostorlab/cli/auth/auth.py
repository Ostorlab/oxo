import logging

import click

from ostorlab.apis import runner as apis_runner
from ostorlab.cli.rootcli import auth

logger = logging.getLogger(__name__)

@auth.command()
@click.option('--username', '-u', help='Ostorlab platform username.', required=True)
@click.option('--password', '-p', help='Ostorlab platform password.', required=True)
@click.option('--expires', '-e', help='Expiration time for token (m for minutes, h for hours, and d for days).')
@click.pass_context
def login(ctx, username, password, expires):
    try:
        api_runner = apis_runner.APIRunner(username=username, password=password,
                                        expires=expires)
        api_runner.authenticate()
    except apis_runner.AuthenticationError:
        logger.error(
            'Authentication error, please check that your credentials are valid.')
