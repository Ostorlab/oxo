"""Module for the ostorlab server run command."""

import click

from ostorlab.cli.server.server import server
from ostorlab.runtimes.local.app import app


@server.group(invoke_without_command=True)
@click.option("--host", default="127.0.0.1", help="The host to run the Flask app on.")
@click.option("--port", default=5000, help="The port to run the Flask app on.")
@click.pass_context
def run(ctx: click.core.Context, host: str, port: int) -> None:
    """Run the Flask server with the specified host and port."""
    app.flask_app.run(host=host, port=port)
