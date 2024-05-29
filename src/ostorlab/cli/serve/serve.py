"""Module for the ostorlab serve command."""

import click

from ostorlab.cli.rootcli import rootcli


@rootcli.command()
@click.option("--host", default="0.0.0.0", help="The host to run the Flask app on.")
@click.option("--port", default=3420, help="The port to run the Flask app on.")
@click.pass_context
def serve(ctx: click.core.Context, host: str, port: int) -> None:
    """Run the Flask serve with the specified host and port."""
    try:
        from ostorlab.serve_app import app
    except ImportError as e:
        missing_dependency = e.name
        raise click.ClickException(
            f"The '{missing_dependency}' package is required for the 'serve' command. "
            f"Please install it using 'pip install ostorlab[serve]'."
        )
    flask_app = app.create_app(graphiql=True)
    flask_app.run(host=host, port=port)
