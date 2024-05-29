import flask
from graphene_file_upload import flask as graphene_upload_flask
import ubjson

from ostorlab.serve_app.schema import schema


def create_app(path: str = "/graphql", **kwargs) -> flask.Flask:
    """Create a Flask app with the specified path."""
    app = flask.Flask(__name__)
    app.add_url_rule(
        path,
        view_func=CustomUBJSONFileUploadGraphQLView.as_view(
            "graphql", schema=schema, **kwargs
        ),
    )
    return app


class CustomUBJSONFileUploadGraphQLView(graphene_upload_flask.FileUploadGraphQLView):
    """Handles application/ubjson content type in flask views"""

    def parse_body(self):
        """Handle application/ubjson content type"""

        content_type = flask.request.mimetype
        if content_type == "application/ubjson":
            return self.ubjson_decode(flask.request)
        return super().parse_body()

    def ubjson_decode(self, request: flask.Request):
        """Decode UBJSON request data."""

        return ubjson.loadb(request.data)
