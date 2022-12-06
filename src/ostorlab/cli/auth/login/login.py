"""Auth login command."""

import logging

import click

from ostorlab.apis.runners import authenticated_runner
from ostorlab.cli.auth import auth
from ostorlab.cli import console as cli_console

logger = logging.getLogger(__name__)
console = cli_console.Console()


@auth.auth.command()
@click.option(
    "--username", "-u", help="Ostorlab platform username.", required=True, prompt=True
)
@click.option(
    "--password",
    "-p",
    help="Ostorlab platform password.",
    required=True,
    prompt=True,
    hide_input=True,
)
@click.option(
    "--token-duration",
    help="Expiration time for token (m for minutes, h for hours, and d for days).",
)
def login(username, password, token_duration):
    """Use this to log into your account."""
    try:
        api_runner = authenticated_runner.AuthenticatedAPIRunner(
            username=username, password=password, token_duration=token_duration
        )
        api_runner.authenticate()
    except authenticated_runner.AuthenticationError:
        console.error(
            "Authentication error, please check that your credentials are valid."
        )
