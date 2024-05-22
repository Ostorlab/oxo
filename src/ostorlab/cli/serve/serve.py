"""Module for the ostorlab serve command."""

import click

from ostorlab.cli.rootcli import rootcli
from ostorlab.runtimes.local.app import app


@rootcli.command()
@click.option("--host", default="0.0.0.0", help="The host to run the Flask app on.")
@click.option("--port", default=3420, help="The port to run the Flask app on.")
@click.pass_context
def serve(ctx: click.core.Context, host: str, port: int) -> None:
    """Run the Flask serve with the specified host and port."""
    flask_app = app.create_app(graphiql=True)
    flask_app.run(host=host, port=port)
