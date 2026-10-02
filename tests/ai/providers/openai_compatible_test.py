"""Unit tests for ostorlab.ai.providers.openai_compatible."""

from __future__ import annotations

import json

import pydantic_ai
import pytest
from pydantic_ai.models import openai as pydantic_openai
from pydantic_ai.models import openrouter as pydantic_openrouter
from pydantic_ai.profiles import openai as openai_profile
from pydantic_ai.providers import openrouter as openrouter_provider
from pytest_httpx import HTTPXMock

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
        ("earthruntime/deepseek-v4-flash", "https://staging.earthruntime.com/v1/"),
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
    ["z_ai/glm-5", "earthruntime/deepseek-v4-flash", "litellm/openrouter/zai/glm-4"],
)
def testBuildModel_whenGatewayProvider_shouldConfigureReasoningContentProfile(
    identifier: str,
) -> None:
    model = factory.build_model(identifier, "k", options=_LITELLM_OPTIONS)

    assert isinstance(model.profile, openai_profile.OpenAIModelProfile)
    assert model.profile.openai_supports_tool_choice_required is False
    assert model.profile.openai_chat_thinking_field == "reasoning_content"
    assert model.profile.openai_chat_send_back_thinking_parts == "field"


@pytest.mark.parametrize("gateway_url", [None, "", "   ", "not a url", "ftp://gateway"])
def testBuildModel_whenLitellmGatewayUrlMissingOrInvalid_shouldRaise(
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
            '{"api_key": "k", "azure_endpoint": "https://a", "api_version": 1}',
            "'api_version' for Azure provider must be a string",
        ),
        ('{"api_key": "k", "azure_endpoint": "not a url"}', "must start with"),
        ('{"api_key": "k", "azure_endpoint": "ftp://a.example"}', "must start with"),
    ],
)
def testBuildModel_whenAzureCredentialInvalid_shouldRaise(
    credential: str, message: str
) -> None:
    with pytest.raises(errors.ModelConfigurationError, match=message):
        factory.build_model("azure_ai_foundry/gpt-5.2", credential)


def testBuildModel_whenAzureEndpointInvalid_shouldNotEchoItInTheError() -> None:
    with pytest.raises(errors.ModelConfigurationError) as exc_info:
        factory.build_model(
            "azure_ai_foundry/gpt-5.2",
            json.dumps({"api_key": "k", "azure_endpoint": "tenant-secret-host"}),
        )

    assert "tenant-secret-host" not in str(exc_info.value)


def testBuildModel_whenAzureEndpointHasSurroundingSpaces_shouldStripThem() -> None:
    model = factory.build_model(
        "azure_ai_foundry/gpt-5.2",
        json.dumps(
            {"api_key": "k", "azure_endpoint": "  https://test.openai.azure.com/ "}
        ),
    )

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert str(model.client.base_url) == "https://test.openai.azure.com/openai/v1/"


@pytest.mark.parametrize("api_version", ["", "   ", None])
def testBuildModel_whenAzureApiVersionBlankOrNull_shouldFallbackToV1Api(
    api_version: str | None,
) -> None:
    """Stored secrets use an empty api_version to mean the v1 GA API."""
    model = factory.build_model(
        "azure_ai_foundry/gpt-5.2",
        json.dumps(
            {
                "api_key": "k",
                "azure_endpoint": "https://test.openai.azure.com/",
                "api_version": api_version,
            }
        ),
    )

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert str(model.client.base_url) == "https://test.openai.azure.com/openai/v1/"


def testBuildModel_whenQwen_shouldTargetDashScopeInternationalByDefault() -> None:
    model = factory.build_model("qwen/qwen3-max", "dashscope-key")

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert model.client.api_key == "dashscope-key"
    assert (
        str(model.client.base_url)
        == "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/"
    )


def testBuildModel_whenQwenBaseUrlConfigured_shouldTargetThatRegion() -> None:
    model = factory.build_model(
        "qwen/qwen3-max",
        "k",
        options=options.ProviderOptions(
            qwen_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        ),
    )

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert (
        str(model.client.base_url)
        == "https://dashscope.aliyuncs.com/compatible-mode/v1/"
    )


@pytest.mark.parametrize("qwen_base_url", ["", "ftp://dashscope"])
def testBuildModel_whenQwenBaseUrlInvalid_shouldRaise(qwen_base_url: str) -> None:
    with pytest.raises(errors.ModelConfigurationError, match="qwen_base_url"):
        factory.build_model(
            "qwen/qwen3-max",
            "k",
            options=options.ProviderOptions(qwen_base_url=qwen_base_url),
        )


def testBuildModel_whenQwenWithoutKey_shouldRaise() -> None:
    with pytest.raises(errors.ModelConfigurationError, match="API key must be set"):
        factory.build_model("qwen/qwen3-max", None)


_OLLAMA_OPTIONS = options.ProviderOptions(ollama_base_url="http://localhost:11434/v1")


@pytest.mark.parametrize("credential", [None, "", "  "])
def testBuildModel_whenOllamaWithoutKey_shouldUsePlaceholderInsteadOfEnvironment(
    monkeypatch: pytest.MonkeyPatch, credential: str | None
) -> None:
    """A local server needs no key; the library must not pick one up from the env."""
    monkeypatch.setenv("OLLAMA_API_KEY", "key-from-environment")

    model = factory.build_model("ollama/qwen3:8b", credential, options=_OLLAMA_OPTIONS)

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert model.model_name == "qwen3:8b"
    assert str(model.client.base_url) == "http://localhost:11434/v1/"
    assert model.client.api_key == "api-key-not-set"


def testBuildModel_whenOllamaWithKey_shouldSendIt() -> None:
    model = factory.build_model(
        "ollama/gpt-oss:120b",
        "ollama-cloud-key",
        options=options.ProviderOptions(ollama_base_url="https://ollama.com/v1"),
    )

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert model.client.api_key == "ollama-cloud-key"


@pytest.mark.parametrize("ollama_base_url", [None, "", "localhost:11434"])
def testBuildModel_whenOllamaBaseUrlMissingOrInvalid_shouldRaise(
    monkeypatch: pytest.MonkeyPatch, ollama_base_url: str | None
) -> None:
    """The OLLAMA_BASE_URL environment variable is not a fallback either."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://from-environment:11434/v1")

    with pytest.raises(errors.ModelConfigurationError, match="ollama_base_url"):
        factory.build_model(
            "ollama/qwen3:8b",
            None,
            options=options.ProviderOptions(ollama_base_url=ollama_base_url),
        )


@pytest.mark.parametrize(
    "model_name",
    ["moonshotai/kimi-k2.6", "google/gemini-3.7-flash", "anthropic/claude-sonnet-4.6"],
)
def testBuildModel_whenOpenRouter_shouldUseNativeModelWithPerModelProfile(
    model_name: str,
) -> None:
    """Each model family keeps its own conventions instead of OpenAI's."""
    model = factory.build_model(f"openrouter/{model_name}", "or-key")

    assert isinstance(model, pydantic_openrouter.OpenRouterModel)
    assert model.system == "openrouter"
    assert model.client.api_key == "or-key"
    assert isinstance(model.profile, openrouter_provider.OpenRouterModelProfile)
    assert model.profile.openai_chat_thinking_field == "reasoning"


@pytest.mark.parametrize(
    "model_name",
    [
        "moonshotai/kimi-k2.5",
        "moonshotai/kimi-k2.6",
        "deepseek/deepseek-v3.2",
        "~moonshotai/kimi-latest",
        "~deepseek/deepseek-pro-latest",
    ],
)
def testBuildModel_whenOpenRouterKimiOrDeepSeek_shouldNotForceToolChoice(
    model_name: str,
) -> None:
    """Both fail on tool_choice=required through OpenRouter (verified live)."""
    model = factory.build_model(f"openrouter/{model_name}", "k")

    assert isinstance(model, pydantic_openrouter.OpenRouterModel)
    assert isinstance(model.profile, openrouter_provider.OpenRouterModelProfile)
    assert model.profile.openai_supports_tool_choice_required is False
    assert model.profile.openai_chat_thinking_field == "reasoning"


@pytest.mark.parametrize(
    "model_name",
    [
        "z-ai/glm-5",
        "google/gemini-3.7-flash",
        "openai/gpt-5.6-luna-pro",
        "~openai/gpt-luna-latest",
    ],
)
def testBuildModel_whenOpenRouterModelIsNotKimiOrDeepSeek_shouldKeepOpenRoutersToolChoice(
    model_name: str,
) -> None:
    model = factory.build_model(f"openrouter/{model_name}", "k")

    assert isinstance(model.profile, openrouter_provider.OpenRouterModelProfile)
    assert model.profile.openai_supports_tool_choice_required is True


_LOCAL_SERVER = options.ProviderOptions(
    openai_compatible_base_url="http://gpu-box:8000/v1"
)


@pytest.mark.parametrize("credential", [None, "", "  "])
def testBuildModel_whenOpenAICompatibleWithoutKey_shouldIgnoreTheOpenAIEnvironment(
    monkeypatch: pytest.MonkeyPatch, credential: str | None
) -> None:
    """A real OPENAI_API_KEY must never be sent to a self-hosted server."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-real-openai-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    model = factory.build_model(
        "openai_compatible/Qwen/Qwen3-32B", credential, options=_LOCAL_SERVER
    )

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert model.model_name == "Qwen/Qwen3-32B"
    assert str(model.client.base_url) == "http://gpu-box:8000/v1/"
    assert model.client.api_key == "api-key-not-set"


def testBuildModel_whenOpenAICompatibleWithKey_shouldSendIt() -> None:
    model = factory.build_model(
        "openai_compatible/meta-llama/Llama-3.3-70B-Instruct",
        "server-token",
        options=_LOCAL_SERVER,
    )

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert model.client.api_key == "server-token"


def testBuildModel_whenOpenAICompatible_shouldUseTheConservativeGatewayProfile() -> (
    None
):
    """Self-hosted servers vary in forced tool-call support (e.g. vLLM tool parsers)."""
    model = factory.build_model(
        "openai_compatible/any-model", None, options=_LOCAL_SERVER
    )

    assert isinstance(model.profile, openai_profile.OpenAIModelProfile)
    assert model.profile.openai_supports_tool_choice_required is False
    assert model.profile.openai_chat_thinking_field == "reasoning_content"


@pytest.mark.parametrize("base_url", [None, "", "gpu-box:8000/v1"])
def testBuildModel_whenOpenAICompatibleBaseUrlMissingOrInvalid_shouldRaise(
    monkeypatch: pytest.MonkeyPatch, base_url: str | None
) -> None:
    """OPENAI_BASE_URL from the environment is not a fallback either."""
    monkeypatch.setenv("OPENAI_BASE_URL", "http://from-environment:8000/v1")

    with pytest.raises(
        errors.ModelConfigurationError, match="openai_compatible_base_url"
    ):
        factory.build_model(
            "openai_compatible/any-model",
            None,
            options=options.ProviderOptions(openai_compatible_base_url=base_url),
        )


def testRunModel_whenOpenAICompatibleWithoutKey_shouldCallTheServerWithoutTheOpenAIKey(
    monkeypatch: pytest.MonkeyPatch, httpx_mock: HTTPXMock
) -> None:
    """End to end: the request reaches the configured server and carries no real key."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-real-openai-key")
    httpx_mock.add_response(
        url="http://gpu-box:8000/v1/chat/completions",
        json={
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 0,
            "model": "Qwen/Qwen3-32B",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "ok"},
                    "finish_reason": "stop",
                }
            ],
        },
    )
    model = factory.build_model(
        "openai_compatible/Qwen/Qwen3-32B", None, options=_LOCAL_SERVER
    )

    pydantic_ai.Agent(model).run_sync("hello")

    request = httpx_mock.get_request()
    assert request is not None
    assert request.method == "POST"
    assert str(request.url) == "http://gpu-box:8000/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer api-key-not-set"
    assert "sk-real-openai-key" not in str(request.headers)


@pytest.mark.parametrize(
    ("identifier", "provider_options"),
    [
        ("openai_compatible/any-model", _LOCAL_SERVER),
        ("ollama/qwen3:8b", _OLLAMA_OPTIONS),
    ],
)
def testBuildModel_whenLocalKeyHasSurroundingWhitespace_shouldSendItStripped(
    identifier: str, provider_options: options.ProviderOptions
) -> None:
    """A pasted key with a trailing newline must not reach the server literally."""
    model = factory.build_model(
        identifier, "  server-token\n", options=provider_options
    )

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert model.client.api_key == "server-token"
