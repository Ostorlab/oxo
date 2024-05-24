import flask
from graphene_file_upload import flask as graphene_upload_flask

from ostorlab.serve_app.schema import schema


def create_app(path: str = "/graphql", **kwargs) -> flask.Flask:
    """Create a Flask app with the specified path."""
    app = flask.Flask(__name__)
    app.add_url_rule(
        path,
        view_func=graphene_upload_flask.FileUploadGraphQLView.as_view(
            "graphql", schema=schema, **kwargs
        ),
    )
    return app
