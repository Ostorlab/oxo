from typing import Optional

import flask
from graphene_file_upload import flask as graphene_upload_flask

from ostorlab.runtimes.local.models import models
from ostorlab.serve_app.schema import schema

AUTHORIZATION_HEADER = "X-API-KEY"


def create_app(path: str = "/graphql", **kwargs) -> flask.Flask:
    """Create a Flask app with the specified path."""
    app = flask.Flask(__name__)
    app.add_url_rule(
        path,
        view_func=graphene_upload_flask.FileUploadGraphQLView.as_view(
            "graphql", schema=schema, **kwargs
        ),
    )

    @app.before_request
    def authenticate() -> Optional[tuple[flask.Response, int]]:
        """Authenticate the request."""
        api_key = flask.request.headers.get(AUTHORIZATION_HEADER)
        if api_key is None or models.APIKey.is_valid(api_key) is False:
            return flask.jsonify({"error": "Unauthorized"}), 401
        else:
            # The request is authenticated. Continue.
            return None

    return app
