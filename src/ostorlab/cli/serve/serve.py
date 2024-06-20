"""Module for the ostorlab serve command."""

import click

from ostorlab.cli import console as cli_console
from ostorlab.cli.rootcli import rootcli
from ostorlab.runtimes.local.models import models

console = cli_console.Console()
DEFAULT_SCANNER_NAME = "Local Scanner"


@rootcli.command()
@click.option("--host", default="0.0.0.0", help="The host to run the Flask app on.")
@click.option("--port", default=3420, help="The port to run the Flask app on.")
@click.option("--refresh-api-key", is_flag=True, help="Generate a new API key.")
@click.pass_context
def serve(ctx: click.core.Context, host: str, port: int, refresh_api_key: bool) -> None:
    """Run the Flask serve with the specified host and port."""
    try:
        from ostorlab.serve_app import app
    except ImportError as e:
        missing_dependency = e.name
        raise click.ClickException(
            f"The '{missing_dependency}' package is required for the 'serve' command. "
            f"Please install it using 'pip install ostorlab[serve]'."
        )
    if refresh_api_key is True:
        api_key = models.APIKey.refresh()
        console.info("API key refreshed")
    else:
        api_key = models.APIKey.get_or_create()
    flask_app = app.create_app(graphiql=True)
    graphql_endpoint = f"http://{host}:{port}/graphql"
    ui_url = f"http://{host}:{port}/"
    scanners_url = f"{ui_url}scanners/new?endpoint={graphql_endpoint}&key={api_key.key}&name={DEFAULT_SCANNER_NAME}"
    console.success(f"Quick start: {scanners_url}")
    console.success(f"To authenticate, please use the following API key: {api_key.key}")
    console.success(f"Serving API on : {graphql_endpoint}")
    console.success(f"Serving UI on : {ui_url}")
    flask_app.run(host=host, port=port)
