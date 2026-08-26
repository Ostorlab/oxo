"""This module is the entry point for OXO CLI."""

import json
import logging

import click

from ostorlab import configuration_manager

logger = logging.getLogger("CLI")

# Namespaces of oxo's own loggers. Raising every registered logger instead buries the output: SQLAlchemy echoes
# each statement and PRAGMA at INFO, and the HTTP clients log a line per request.
OXO_LOGGERS = ("ostorlab", "CLI")


def _set_loggers_level(level: int) -> None:
    """Raise the verbosity of oxo's own loggers, leaving third-party ones at their configured level.

    Args:
        level: The logging level to apply.
    """
    for name in list(logging.root.manager.loggerDict):
        if name.startswith(OXO_LOGGERS) is False:
            continue
        logging.getLogger(name).setLevel(level)


@click.group()
@click.pass_context
@click.version_option()
@click.option("--api-key", help="API key to login to the platform.", required=False)
@click.option("--proxy", "-X", help="Proxy to route HTTPS requests through.")
@click.option(
    "--tlsverify/--no-tlsverify",
    help="Control TLS server certificate verification.",
    default=True,
)
@click.option("-d", "--debug/--no-debug", help="Enable debug mode", default=False)
@click.option("-v", "--verbose/--no-verbose", help="Enable verbose mode", default=False)
@click.option(
    "--gcp-logging-credential",
    type=click.Path(exists=True),
    help="Path to GCP logging JSON credential file.",
    required=False,
)
def rootcli(
    ctx: click.core.Context,
    proxy: str | None = None,
    tlsverify: bool | None = True,
    debug: bool = False,
    verbose: bool = False,
    api_key: str | None = None,
    gcp_logging_credential: str | None = None,
) -> None:
    """Oxo is an open-source project to help automate security testing.\n
    Oxo standardizes interoperability between tools in a consistent, scalable, and performant way.
    """
    ctx.obj = {}
    ctx.obj["proxy"] = proxy
    ctx.obj["tlsverify"] = tlsverify
    ctx.obj["api_key"] = api_key
    # Configuration is a singleton class. One initiated with the provided API key, others will make use of it.
    conf_manager = configuration_manager.ConfigurationManager()
    conf_manager.api_key = api_key
    ctx.obj["config_manager"] = conf_manager

    if verbose is True:
        _set_loggers_level(logging.INFO)
    if debug is True:
        _set_loggers_level(logging.DEBUG)
    if gcp_logging_credential is not None:
        try:
            import google.cloud.logging
            from google.oauth2 import service_account

            with open(gcp_logging_credential, "r", encoding="utf-8") as source:
                content = source.read()
                info = json.loads(content)

            credentials = service_account.Credentials.from_service_account_info(info)
            client = google.cloud.logging.Client(credentials=credentials)
            client.setup_logging()
            ctx.obj["gcp_logging_credential"] = content
        except ImportError:
            logger.error(
                "Could not import Google Cloud Logging, install it with `pip install 'ostorlab[google-cloud-logging]'"
            )
