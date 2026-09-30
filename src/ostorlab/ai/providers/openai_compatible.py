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
            http_client=request.options.http_client_for(request.provider),
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
    if request.options.litellm_gateway_url is None:
        raise errors.ModelConfigurationError(
            "litellm_gateway_url must be set when using litellm provider"
        )
    return _build_gateway_model(request, request.options.litellm_gateway_url)


def build_deepseek(request: base.BuildRequest) -> models.Model:
    """Build a DeepSeek model."""
    return openai.OpenAIChatModel(
        model_name=request.model_name,
        provider=deepseek_provider.DeepSeekProvider(
            api_key=request.credential,
            http_client=request.options.http_client_for(request.provider),
        ),
        settings=request.settings,
    )


def build_moonshotai(request: base.BuildRequest) -> models.Model:
    """Build a MoonshotAI (Kimi) model."""
    return openai.OpenAIChatModel(
        model_name=request.model_name,
        provider=_build_moonshotai_provider(request),
        settings=request.settings,
    )


def build_fireworks(request: base.BuildRequest) -> models.Model:
    """Build a Fireworks model, keeping pydantic-ai's per-model profile."""
    return openai.OpenAIChatModel(
        model_name=request.model_name,
        provider=_build_fireworks_provider(request),
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
    http_client = request.options.http_client_for(request.provider)
    if creds.get("api_version") is not None:
        return openai.OpenAIChatModel(
            model_name=request.model_name,
            provider=azure_provider.AzureProvider(
                azure_endpoint=creds["azure_endpoint"],
                api_key=creds["api_key"],
                api_version=creds["api_version"],
                http_client=http_client,
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
            base_url=creds["azure_endpoint"].rstrip("/") + "/" + AZURE_V1_PATH,
            api_key=creds["api_key"],
            http_client=http_client,
        ),
        settings=request.settings,
    )


def _build_gateway_model(request: base.BuildRequest, base_url: str) -> models.Model:
    return openai.OpenAIChatModel(
        model_name=request.model_name,
        provider=openai_provider.OpenAIProvider(
            api_key=request.credential,
            base_url=base_url,
            http_client=request.options.http_client_for(request.provider),
        ),
        profile=base.reasoning_content_profile(supports_tool_choice_required=False),
        settings=request.settings,
    )


# MoonshotAI and Fireworks type ``http_client`` as non-optional in their overloads,
# so it is only passed when a timeout is configured.
def _build_moonshotai_provider(
    request: base.BuildRequest,
) -> moonshotai_provider.MoonshotAIProvider:
    http_client = request.options.http_client_for(request.provider)
    if http_client is None:
        return moonshotai_provider.MoonshotAIProvider(api_key=request.credential)
    return moonshotai_provider.MoonshotAIProvider(
        api_key=request.credential, http_client=http_client
    )


def _build_fireworks_provider(
    request: base.BuildRequest,
) -> fireworks_provider.FireworksProvider:
    http_client = request.options.http_client_for(request.provider)
    if http_client is None:
        return fireworks_provider.FireworksProvider(api_key=request.credential)
    return fireworks_provider.FireworksProvider(
        api_key=request.credential, http_client=http_client
    )
