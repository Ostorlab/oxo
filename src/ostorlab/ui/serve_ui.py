import http.server
import pathlib

from ostorlab.cli import console as cli_console

console = cli_console.Console()

UI_STATIC_FILES_DIRECTORY = pathlib.Path(__file__).parent / "static_files"


def start_server(host: str = "", port: int = 8000):
    """Start a simple HTTP server serving the files in the specified directory.
    Args:
        host: The host to serve the files on.
        port: The port to serve the files on.
    """

    class StaticFileHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        """Custom HTTP request handler to serve static files."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(UI_STATIC_FILES_DIRECTORY), **kwargs)

        def log_message(self, *args):
            """Suppress logging of HTTP requests."""
            pass

    try:
        console.success(f"Serving UI on : http://{host}:{port} ...")
        httpd = http.server.HTTPServer((host, port), StaticFileHTTPRequestHandler)
        httpd.serve_forever()
    except Exception as e:
        console.error(f"Failed to start the server: {e}")
