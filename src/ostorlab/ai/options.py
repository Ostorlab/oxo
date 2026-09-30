"""Deployment-wide options some providers need besides the credential."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping

import httpx


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class ProviderOptions:
    """Options that are not per-model secrets but deployment configuration.

    Attributes:
        litellm_gateway_url: Base URL of the LiteLLM gateway, required by ``litellm``.
        vertex_endpoint_url: URL of the self-deployed Vertex endpoint, required by
            ``google_vertex_endpoint``. Must not end with a trailing slash.
        http_timeouts: Per-provider HTTP timeouts, keyed by canonical provider name
            (e.g. ``{"google": httpx.Timeout(250, connect=5)}``). Providers without an
            entry use their SDK's default HTTP client.
    """

    litellm_gateway_url: str | None = None
    vertex_endpoint_url: str | None = None
    http_timeouts: Mapping[str, httpx.Timeout | float] = dataclasses.field(
        default_factory=dict
    )

    def http_client_for(self, provider: str) -> httpx.AsyncClient | None:
        """Return a fresh HTTP client honouring the provider's timeout, if one is set."""
        timeout = self.http_timeouts.get(provider)
        if timeout is None:
            return None
        return httpx.AsyncClient(timeout=timeout)
