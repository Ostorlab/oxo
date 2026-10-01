"""Providers served through an OpenAI-compatible API."""

from __future__ import annotations

import logging

from pydantic_ai import models
from pydantic_ai.models import openai
from pydantic_ai.providers import azure as azure_provider
from pydantic_ai.providers import deepseek as deepseek_provider
from pydantic_ai.providers import fireworks as fireworks_provider
from pydantic_ai.providers import moonshotai as moonshotai_provider
from pydantic_ai.providers import openai as openai_provider

from ostorlab.ai import credentials
from ostorlab.ai import errors
from ostorlab.ai.providers import base

logger = logging.getLogger(__name__)

OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
Z_AI_BASE_URL = "https://api.z.ai/api/paas/v4"

# Path appended to an Azure OpenAI endpoint to reach the v1 GA API, which is
# OpenAI-client compatible and needs no dated ``api-version``.
AZURE_V1_PATH = "openai/v1/"


def build_openai(request: base.BuildRequest) -> models.Model:
    """Build an OpenAI model on the Responses API."""
    return openai.OpenAIResponsesModel(
        model_name=request.model_name,
        provider=openai_provider.OpenAIProvider(
            api_key=request.credential,
            base_url=OPENAI_BASE_URL,
        ),
        settings=request.settings,
    )


def build_openrouter(request: base.BuildRequest) -> models.Model:
    """Build an OpenRouter model, exposing reasoning under ``reasoning_content``."""
    return _build_gateway_model(request, OPENROUTER_BASE_URL)


def build_z_ai(request: base.BuildRequest) -> models.Model:
    """Build a z.ai model, exposing reasoning under ``reasoning_content``."""
    return _build_gateway_model(request, Z_AI_BASE_URL)


def build_litellm(request: base.BuildRequest) -> models.Model:
    """Build a model routed through the LiteLLM gateway.

    LiteLLM proxies many upstream providers, so the reasoning profile is set
    unconditionally, as for OpenRouter.
    """
    gateway_url = (request.options.litellm_gateway_url or "").strip()
    if gateway_url == "":
        raise errors.ModelConfigurationError(
            "litellm_gateway_url must be set when using litellm provider"
        )
    if gateway_url.startswith(("http://", "https://")) is False:
        raise errors.ModelConfigurationError(
            f"litellm_gateway_url must start with 'http://' or 'https://', got: {gateway_url!r}."
        )
    return _build_gateway_model(request, gateway_url)


def build_deepseek(request: base.BuildRequest) -> models.Model:
    """Build a DeepSeek model."""
    return openai.OpenAIChatModel(
        model_name=request.model_name,
        provider=deepseek_provider.DeepSeekProvider(
            api_key=request.credential,
        ),
        settings=request.settings,
    )


def build_moonshotai(request: base.BuildRequest) -> models.Model:
    """Build a MoonshotAI (Kimi) model."""
    return openai.OpenAIChatModel(
        model_name=request.model_name,
        provider=moonshotai_provider.MoonshotAIProvider(api_key=request.credential),
        settings=request.settings,
    )


def build_fireworks(request: base.BuildRequest) -> models.Model:
    """Build a Fireworks model, keeping pydantic-ai's per-model profile."""
    return openai.OpenAIChatModel(
        model_name=request.model_name,
        provider=fireworks_provider.FireworksProvider(api_key=request.credential),
        settings=request.settings,
    )


def build_azure_ai_foundry(request: base.BuildRequest) -> models.Model:
    """Build an Azure AI Foundry model from ``{"azure_endpoint", "api_key", "api_version"?}``.

    Without ``api_version`` the v1 GA API is used, reached through the plain OpenAI
    client since it needs no dated version.
    """
    creds = credentials.parse_json_object(
        request.credential, "Azure provider", request.model_name
    )
    credentials.require_keys(creds, ["azure_endpoint", "api_key"], "Azure provider")
    credentials.require_non_empty_strings(
        creds, ["azure_endpoint", "api_key"], "Azure provider"
    )
    azure_endpoint = creds["azure_endpoint"].strip()
    # The endpoint is part of the credential, so it is not echoed in the error.
    if azure_endpoint.startswith(("http://", "https://")) is False:
        raise errors.ModelConfigurationError(
            "Credential 'azure_endpoint' for Azure provider must start with "
            f"'http://' or 'https://' (model={request.model_name})."
        )
    # A blank api_version means "use the v1 API", as the agents stored it before.
    api_version = creds.get("api_version")
    if isinstance(api_version, str) is False and api_version is not None:
        raise errors.ModelConfigurationError(
            f"Credential 'api_version' for Azure provider must be a string (model={request.model_name})."
        )
    if api_version is not None and api_version.strip() != "":
        return openai.OpenAIChatModel(
            model_name=request.model_name,
            provider=azure_provider.AzureProvider(
                azure_endpoint=azure_endpoint,
                api_key=creds["api_key"],
                api_version=api_version.strip(),
            ),
            settings=request.settings,
        )
    logger.warning(
        "No api_version in Azure credentials; falling back to the v1 GA API (%s).",
        AZURE_V1_PATH,
    )
    return openai.OpenAIChatModel(
        model_name=request.model_name,
        provider=openai_provider.OpenAIProvider(
            base_url=azure_endpoint.rstrip("/") + "/" + AZURE_V1_PATH,
            api_key=creds["api_key"],
        ),
        settings=request.settings,
    )


def _build_gateway_model(request: base.BuildRequest, base_url: str) -> models.Model:
    return openai.OpenAIChatModel(
        model_name=request.model_name,
        provider=openai_provider.OpenAIProvider(
            api_key=request.credential,
            base_url=base_url,
        ),
        profile=base.reasoning_content_profile(supports_tool_choice_required=False),
        settings=request.settings,
    )
