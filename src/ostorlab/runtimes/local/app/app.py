import flask
from graphene_file_upload import flask as graphene_upload_flask

from ostorlab.runtimes.local.app.schema import schema

flask_app = flask.Flask(__name__)

flask_app.add_url_rule(
    "/oxo_graphql",
    view_func=graphene_upload_flask.FileUploadGraphQLView.as_view(
        "oxo_graphql", schema=schema, graphiql=True
    ),
)
