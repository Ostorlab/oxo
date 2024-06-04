import functools

from typing import Optional

import flask
import flask_cors
import graphql_server
from graphene_file_upload import flask as graphene_upload_flask
import ubjson

from ostorlab.runtimes.local.models import models
from ostorlab.serve_app.schema import schema

AUTHORIZATION_HEADER = "X-API-KEY"


def create_app(path: str = "/graphql", **kwargs) -> flask.Flask:
    """Create a Flask app with the specified path."""
    app = flask.Flask(__name__)
    flask_cors.CORS(app, resources={r"/graphql": {"origins": "*"}})
    app.add_url_rule(
        path,
        view_func=CustomUBJSONFileUploadGraphQLView.as_view(
            "graphql", schema=schema, **kwargs
        ),
    )

    @app.before_request
    def authenticate() -> Optional[tuple[flask.Response, int]]:
        """Authenticate the request."""
        api_key = flask.request.headers.get(AUTHORIZATION_HEADER)
        if flask.request.method == "OPTIONS":
            # CORS requires sending an initial OPTIONS that should return 200 OK.
            return None

        if api_key is None or models.APIKey.is_valid(api_key) is False:
            return flask.jsonify({"error": "Unauthorized"}), 401
        else:
            # The request is authenticated. Continue.
            return None

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

    def dispatch_request(self) -> flask.Response:
        try:
            request_method = flask.request.method.lower()
            data = self.parse_body()

            show_graphiql = request_method == "get" and self.should_display_graphiql()
            catch = show_graphiql

            pretty = self.pretty or show_graphiql or flask.request.args.get("pretty")

            extra_options = {}
            executor = self.get_executor()
            if executor is not None:
                extra_options["executor"] = executor

            execution_results, all_params = graphql_server.run_http_query(
                self.schema,
                request_method,
                data,
                query_data=flask.request.args,
                batch_enabled=self.batch,
                catch=catch,
                backend=self.get_backend(),
                root=self.get_root_value(),
                context=self.get_context(),
                middleware=self.get_middleware(),
                **extra_options,
            )

            content_type = "application/json"
            if flask.request.mimetype == "application/ubjson":
                result, status_code = graphql_server.encode_execution_results(
                    execution_results,
                    is_batch=isinstance(data, list),
                    format_error=self.format_error,
                    encode=functools.partial(ubjson.dumpb),
                )
                content_type = "application/ubjson"
            else:
                result, status_code = graphql_server.encode_execution_results(
                    execution_results,
                    is_batch=isinstance(data, list),
                    format_error=self.format_error,
                    encode=functools.partial(self.encode, pretty=pretty),
                )

            if show_graphiql is True:
                return self.render_graphiql(params=all_params[0], result=result)

            return flask.Response(result, status=status_code, content_type=content_type)

        except graphql_server.HttpQueryError as e:
            return flask.Response(
                self.encode({"errors": [self.format_error(e)]}),
                status=e.status_code,
                headers=e.headers,
                content_type="application/json",
            )
