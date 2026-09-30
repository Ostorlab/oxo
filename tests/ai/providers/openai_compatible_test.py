"""Unit tests for ostorlab.ai.providers.openai_compatible."""

from __future__ import annotations

import json

import pytest
from pydantic_ai.models import openai as pydantic_openai
from pydantic_ai.profiles import openai as openai_profile

from ostorlab.ai import errors
from ostorlab.ai import factory
from ostorlab.ai import options

_LITELLM_OPTIONS = options.ProviderOptions(
    litellm_gateway_url="https://litellm.example.com/v1"
)


@pytest.mark.parametrize(
    ("identifier", "expected_base_url"),
    [
        ("openai/gpt-5.2", "https://api.openai.com/v1/"),
        ("openrouter/moonshotai/kimi-k2.6", "https://openrouter.ai/api/v1/"),
        ("z_ai/glm-5", "https://api.z.ai/api/paas/v4/"),
        ("litellm/openrouter/zai/glm-4", "https://litellm.example.com/v1/"),
    ],
)
def testBuildModel_whenOpenAICompatibleProvider_shouldTargetItsEndpointWithTheKey(
    identifier: str, expected_base_url: str
) -> None:
    model = factory.build_model(identifier, "the-key", options=_LITELLM_OPTIONS)

    assert isinstance(
        model, pydantic_openai.OpenAIChatModel | pydantic_openai.OpenAIResponsesModel
    )
    assert str(model.client.base_url) == expected_base_url
    assert model.client.api_key == "the-key"


@pytest.mark.parametrize(
    "identifier",
    ["openrouter/moonshotai/kimi-k2.6", "z_ai/glm-5", "litellm/openrouter/zai/glm-4"],
)
def testBuildModel_whenGatewayProvider_shouldConfigureReasoningContentProfile(
    identifier: str,
) -> None:
    model = factory.build_model(identifier, "k", options=_LITELLM_OPTIONS)

    assert isinstance(model.profile, openai_profile.OpenAIModelProfile)
    assert model.profile.openai_supports_tool_choice_required is False
    assert model.profile.openai_chat_thinking_field == "reasoning_content"
    assert model.profile.openai_chat_send_back_thinking_parts == "field"


@pytest.mark.parametrize("gateway_url", [None, "", "   "])
def testBuildModel_whenLitellmWithoutGatewayUrl_shouldRaise(
    gateway_url: str | None,
) -> None:
    with pytest.raises(errors.ModelConfigurationError, match="litellm_gateway_url"):
        factory.build_model(
            "litellm/openrouter/zai/glm-4",
            "k",
            options=options.ProviderOptions(litellm_gateway_url=gateway_url),
        )


def testBuildModel_whenFireworks_shouldUseFireworksEndpointAndKey() -> None:
    model = factory.build_model(
        "fireworks/accounts/fireworks/models/llama-v3p3-70b-instruct", "fw-key"
    )

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert model.client.api_key == "fw-key"
    assert str(model.client.base_url).startswith(
        "https://api.fireworks.ai/inference/v1"
    )
    assert isinstance(model.profile, openai_profile.OpenAIModelProfile)
    assert model.profile.supports_thinking is False


def testBuildModel_whenFireworksDeepSeekR1_shouldKeepPydanticAiThinkingProfile() -> (
    None
):
    model = factory.build_model("fireworks/accounts/fireworks/models/deepseek-r1", "k")

    assert isinstance(model.profile, openai_profile.OpenAIModelProfile)
    assert model.profile.supports_thinking is True
    assert model.profile.openai_chat_send_back_thinking_parts == "auto"


def testBuildModel_whenAzureWithApiVersion_shouldUseTheAzureDeployment() -> None:
    model = factory.build_model(
        "azure_ai_foundry/gpt-5.2",
        json.dumps(
            {
                "api_key": "k",
                "azure_endpoint": "https://test.openai.azure.com",
                "api_version": "2024-10-21",
            }
        ),
    )

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert str(model.client.base_url).startswith("https://test.openai.azure.com/")
    assert str(model.client.base_url).endswith("/openai/v1/") is False


def testBuildModel_whenAzureWithoutApiVersion_shouldFallbackToV1Api() -> None:
    model = factory.build_model(
        "azure_ai_foundry/gpt-5.2",
        json.dumps(
            {"api_key": "k", "azure_endpoint": "https://test.openai.azure.com/"}
        ),
    )

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert str(model.client.base_url) == "https://test.openai.azure.com/openai/v1/"


@pytest.mark.parametrize(
    ("credential", "message"),
    [
        ("{not json", "Invalid JSON"),
        ("[1]", "must be a JSON object"),
        ('{"api_key": "k"}', "azure_endpoint"),
        ("{}", "azure_endpoint, api_key"),
        ('{"api_key": "k", "azure_endpoint": 1}', "non-empty strings: azure_endpoint"),
        (
            '{"api_key": " ", "azure_endpoint": "https://a"}',
            "non-empty strings: api_key",
        ),
        (
            '{"api_key": "k", "azure_endpoint": "https://a", "api_version": ""}',
            "non-empty strings: api_version",
        ),
    ],
)
def testBuildModel_whenAzureCredentialInvalid_shouldRaise(
    credential: str, message: str
) -> None:
    with pytest.raises(errors.ModelConfigurationError, match=message):
        factory.build_model("azure_ai_foundry/gpt-5.2", credential)
