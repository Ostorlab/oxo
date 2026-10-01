"""Build a pydantic-ai model from a ``provider/model`` identifier and its credential.

Adding a provider means writing one builder in ``ostorlab.ai.providers`` and
registering it in ``_BUILDERS``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from pydantic_ai import models
from pydantic_ai import settings as pydantic_ai_settings

from ostorlab.ai import errors
from ostorlab.ai import options as options_module
from ostorlab.ai import settings as settings_module
from ostorlab.ai.providers import anthropic
from ostorlab.ai.providers import base
from ostorlab.ai.providers import bedrock
from ostorlab.ai.providers import google
from ostorlab.ai.providers import openai_compatible
from ostorlab.ai.providers import vertex_endpoint
from ostorlab.ai.providers import xai

_BUILDERS: Final[Mapping[str, base.Builder]] = {
    "anthropic": anthropic.build_anthropic,
    "aws_bedrock": bedrock.build_aws_bedrock,
    "azure_ai_foundry": openai_compatible.build_azure_ai_foundry,
    "deepseek": openai_compatible.build_deepseek,
    "fireworks": openai_compatible.build_fireworks,
    "google": google.build_google,
    "google_vertex": google.build_google_vertex,
    "google_vertex_endpoint": vertex_endpoint.build_google_vertex_endpoint,
    "litellm": openai_compatible.build_litellm,
    "moonshotai": openai_compatible.build_moonshotai,
    "openai": openai_compatible.build_openai,
    "openrouter": openai_compatible.build_openrouter,
    "xai": xai.build_xai,
    "z_ai": openai_compatible.build_z_ai,
}

PROVIDER_ALIASES: Final[Mapping[str, str]] = {"gemini": "google"}

SUPPORTED_PROVIDERS: Final[tuple[str, ...]] = tuple(sorted(_BUILDERS))


def canonical_provider(provider: str) -> str:
    """Resolve a provider alias (e.g. ``gemini``) to its canonical name."""
    return PROVIDER_ALIASES.get(provider, provider)


def parse_identifier(model_identifier: str) -> tuple[str, str]:
    """Split ``provider/model`` into the canonical provider and the model name.

    Only the first ``/`` separates the provider, so model names may contain slashes
    (``openrouter/moonshotai/kimi-k2.6``).

    Raises:
        ModelConfigurationError: If the identifier has no provider or model part.
    """
    raw_provider, separator, raw_model_name = model_identifier.partition("/")
    provider = raw_provider.strip()
    model_name = raw_model_name.strip()
    if separator == "" or provider == "" or model_name.strip("/") == "":
        raise errors.ModelConfigurationError(
            f"Model identifier must be 'provider/model', got: {model_identifier!r}."
        )
    return canonical_provider(provider), model_name


def build_model(
    model_identifier: str,
    credential: str | None,
    *,
    options: options_module.ProviderOptions | None = None,
    settings: pydantic_ai_settings.ModelSettings | None = None,
) -> models.Model:
    """Build the pydantic-ai model for ``model_identifier``.

    Args:
        model_identifier: ``provider/model``, e.g. ``anthropic/claude-sonnet-4-6``.
        credential: The provider secret. A plain API key, or a JSON object for
            ``aws_bedrock``, ``azure_ai_foundry``, ``google_vertex`` (service account
            form) and ``google_vertex_endpoint`` (service-account JSON).
        options: Deployment-wide provider options (gateway and endpoint URLs).
        settings: Model settings; defaults to ``default_settings()``.

    Returns:
        The model, ready to hand to a pydantic-ai ``Agent``.

    Raises:
        ModelConfigurationError: If the provider is unknown, the credential is
            missing or malformed, or a required option is not set.
    """
    provider, model_name = parse_identifier(model_identifier)
    builder = _BUILDERS.get(provider)
    if builder is None:
        raise errors.ModelConfigurationError(
            f"No Provider found for {provider} and model {model_name}."
        )
    if credential is None or credential.strip() == "":
        raise errors.ModelConfigurationError(
            f"API key must be set for provider: {provider}"
        )
    return builder(
        base.BuildRequest(
            provider=provider,
            model_name=model_name,
            credential=credential,
            options=options
            if options is not None
            else options_module.ProviderOptions(),
            settings=settings
            if settings is not None
            else settings_module.default_settings(),
        )
    )
