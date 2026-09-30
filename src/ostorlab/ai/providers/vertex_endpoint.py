"""Customer models self-deployed on a Vertex AI endpoint (OpenAI-compatible route)."""

from __future__ import annotations

import functools
import threading

from google.auth.transport import requests as google_auth_requests
from google.oauth2 import service_account
from pydantic_ai import models
from pydantic_ai.models import openai
from pydantic_ai.providers import openai as openai_provider

from ostorlab.ai import credentials
from ostorlab.ai import errors
from ostorlab.ai.providers import base
from ostorlab.ai.providers import google as google_builders

_PROVIDER_LABEL = "Google Vertex endpoint provider"


class VertexEndpointTokenProvider:
    """Mint and cache the short-lived Google OAuth token for a self-deployed Vertex endpoint.

    Vertex issues no static API key for self-deployed endpoints: callers present an OAuth
    bearer token minted from a service account, valid for roughly an hour. The token is
    therefore refreshed lazily here (on demand, guarded by a lock) rather than resolved
    once and baked into a model for its whole lifetime, since scans outlive it.
    """

    def __init__(
        self, service_account_credentials: service_account.Credentials
    ) -> None:
        self._credentials = service_account_credentials
        self._lock = threading.Lock()

    @property
    def bearer_token(self) -> str:
        """Return a currently-valid bearer token, refreshing it first if needed."""
        with self._lock:
            if self._credentials.valid is False:
                self._credentials.refresh(google_auth_requests.Request())  # type: ignore[no-untyped-call]
            token = self._credentials.token
            if token is None:
                raise errors.ModelConfigurationError(
                    "Google Vertex endpoint credentials produced no access token."
                )
            return str(token)


@functools.cache
def get_token_provider(service_account_credential: str) -> VertexEndpointTokenProvider:
    """Build, once per distinct credential, the shared token provider for an endpoint.

    Parsing the service-account key is moderately expensive, so this is cached on the
    raw credential string and shared across every model rebuilt for that credential.
    """
    service_account_info = credentials.parse_json_object(
        service_account_credential, _PROVIDER_LABEL, "google_vertex_endpoint"
    )
    return VertexEndpointTokenProvider(
        google_builders.build_service_account_credentials(
            service_account_info,
            model="google_vertex_endpoint",
            provider_label=_PROVIDER_LABEL,
        )
    )


class VertexEndpointModel(openai.OpenAIChatModel):
    """An OpenAIChatModel for a self-deployed Vertex endpoint that can rebuild itself.

    Its provider carries a static bearer token baked in at construction time, which
    lets ``OpenAIProvider`` own its httpx client's lifecycle as for every other
    provider. Call ``refresh()`` before each independent run to get a sibling model
    with a currently-valid token and a client bound to the current event loop.
    """

    _build_request: base.BuildRequest

    def refresh(self) -> models.Model:
        """Build a sibling model with a currently-valid token and its own httpx client."""
        return build_google_vertex_endpoint(self._build_request)


def build_google_vertex_endpoint(request: base.BuildRequest) -> models.Model:
    """Build a model backed by a model deployed on a Vertex AI endpoint.

    The credential is the plain service-account JSON; the endpoint URL comes from
    ``ProviderOptions.vertex_endpoint_url``.
    """
    endpoint_url = (request.options.vertex_endpoint_url or "").strip()
    if endpoint_url == "":
        raise errors.ModelConfigurationError(
            "vertex_endpoint_url must be set when using google_vertex_endpoint provider"
        )
    if endpoint_url.endswith("/"):
        raise errors.ModelConfigurationError(
            f"vertex_endpoint_url must not end with a trailing slash, got: {endpoint_url!r}."
        )
    if endpoint_url.startswith(("http://", "https://")) is False:
        raise errors.ModelConfigurationError(
            "vertex_endpoint_url must start with 'http://' or 'https://' "
            f"got: {endpoint_url!r}."
        )

    token = get_token_provider(request.credential.strip()).bearer_token
    model = VertexEndpointModel(
        model_name=request.model_name,
        provider=openai_provider.OpenAIProvider(
            base_url=endpoint_url,
            api_key=token,
            http_client=request.options.http_client_for(request.provider),
        ),
        settings=request.settings,
        profile=base.reasoning_content_profile(supports_tool_choice_required=True),
    )
    model._build_request = request
    return model
