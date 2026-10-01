"""Deployment-wide options some providers need besides the credential."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class ProviderOptions:
    """Options that are not per-model secrets but deployment configuration.

    Request timeouts are not configured here: pydantic-ai sends
    ``ModelSettings.timeout`` with every request, which overrides any HTTP client
    timeout. Pass ``settings.default_settings(timeout=...)`` instead.

    Attributes:
        litellm_gateway_url: Base URL of the LiteLLM gateway, required by ``litellm``.
        vertex_endpoint_url: URL of the self-deployed Vertex endpoint, required by
            ``google_vertex_endpoint``. Must not end with a trailing slash.
    """

    litellm_gateway_url: str | None = None
    vertex_endpoint_url: str | None = None
