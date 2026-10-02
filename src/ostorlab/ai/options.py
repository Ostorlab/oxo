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
        ollama_base_url: OpenAI-compatible base URL of the Ollama server, required by
            ``ollama`` (e.g. ``http://localhost:11434/v1``).
        openai_compatible_base_url: Base URL of any OpenAI-compatible server, required
            by ``openai_compatible`` (e.g. ``http://localhost:8000/v1`` for vLLM).
        qwen_base_url: DashScope base URL for ``qwen``. Defaults to the international
            endpoint; DashScope keys are region-bound, so keys from another region
            need that region's URL.
    """

    litellm_gateway_url: str | None = None
    vertex_endpoint_url: str | None = None
    ollama_base_url: str | None = None
    openai_compatible_base_url: str | None = None
    qwen_base_url: str | None = None
