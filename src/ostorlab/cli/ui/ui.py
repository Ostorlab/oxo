import click

from ostorlab.cli.rootcli import rootcli
from ostorlab.ui import serve_ui


@rootcli.command()
@click.option("--host", default="0.0.0.0", help="The host to run the Flask app on.")
@click.option("--port", default=3421, help="The port to run the Flask app on.")
@click.pass_context
def ui(ctx: click.core.Context, host: str, port: int) -> None:
    """Start the UI server.
    Args:
        ctx: The click context.
        host: The host to run the ui server.
        port: The port to run the ui server.
    """
    serve_ui.start_server(host=host, port=port)
