"""Unit tests for ostorlab.ai.factory."""

from __future__ import annotations

import json

import pytest
from pydantic_ai.models import anthropic as pydantic_anthropic
from pydantic_ai.models import bedrock as pydantic_bedrock
from pydantic_ai.models import google as pydantic_google
from pydantic_ai.models import openai as pydantic_openai
from pydantic_ai.models import xai as pydantic_xai

from ostorlab.ai import errors
from ostorlab.ai import factory
from ostorlab.ai import options
from ostorlab.ai import settings
from tests.ai import conftest

_AZURE_CREDENTIAL = json.dumps(
    {"api_key": "fake-key", "azure_endpoint": "https://test.openai.azure.com/"}
)

_BUILD_CASES = [
    ("openai/gpt-5.2", "k", pydantic_openai.OpenAIResponsesModel, "gpt-5.2"),
    (
        "openrouter/meta-llama/llama-3.3-70b-instruct",
        "k",
        pydantic_openai.OpenAIChatModel,
        "meta-llama/llama-3.3-70b-instruct",
    ),
    ("moonshotai/kimi-k2.5", "k", pydantic_openai.OpenAIChatModel, "kimi-k2.5"),
    ("google/gemini-3.7-flash", "k", pydantic_google.GoogleModel, "gemini-3.7-flash"),
    ("gemini/gemini-3.7-flash", "k", pydantic_google.GoogleModel, "gemini-3.7-flash"),
    ("google_vertex/gemini-3.1", "k", pydantic_google.GoogleModel, "gemini-3.1"),
    ("deepseek/deepseek-chat", "k", pydantic_openai.OpenAIChatModel, "deepseek-chat"),
    ("xai/grok-4.5", "k", pydantic_xai.XaiModel, "grok-4.5"),
    (
        "anthropic/claude-sonnet-4-6",
        "k",
        pydantic_anthropic.AnthropicModel,
        "claude-sonnet-4-6",
    ),
    (
        "azure_ai_foundry/gpt-5.2",
        _AZURE_CREDENTIAL,
        pydantic_openai.OpenAIChatModel,
        "gpt-5.2",
    ),
    (
        "litellm/openrouter/zai/glm-4",
        "k",
        pydantic_openai.OpenAIChatModel,
        "openrouter/zai/glm-4",
    ),
    ("z_ai/some-model", "k", pydantic_openai.OpenAIChatModel, "some-model"),
    (
        "fireworks/accounts/fireworks/models/llama-v3p3-70b-instruct",
        "k",
        pydantic_openai.OpenAIChatModel,
        "accounts/fireworks/models/llama-v3p3-70b-instruct",
    ),
    (
        "aws_bedrock/anthropic.claude-sonnet-4-6",
        json.dumps({"api_key": "k", "region": "us-east-1"}),
        pydantic_bedrock.BedrockConverseModel,
        "anthropic.claude-sonnet-4-6",
    ),
]


@pytest.mark.parametrize(
    ("model_identifier", "credential", "expected_model_type", "expected_model_name"),
    _BUILD_CASES,
)
def testBuildModel_whenProviderIsValid_shouldReturnCorrectModelType(
    model_identifier: str,
    credential: str,
    expected_model_type: type,
    expected_model_name: str,
) -> None:
    model = factory.build_model(
        model_identifier,
        credential,
        options=options.ProviderOptions(
            litellm_gateway_url="https://litellm.example.com/v1"
        ),
    )

    assert isinstance(model, expected_model_type) is True
    assert model.model_name == expected_model_name


def testSupportedProviders_whenCompared_shouldAllBeCoveredByTheBuildCases() -> None:
    """Fails when a builder is registered without a case in ``_BUILD_CASES``.

    ``google_vertex_endpoint`` needs a service account and an endpoint URL, so it is
    covered in ``providers/vertex_endpoint_test.py``.
    """
    covered = {factory.parse_identifier(case[0])[0] for case in _BUILD_CASES}

    assert set(factory.SUPPORTED_PROVIDERS) == covered | {"google_vertex_endpoint"}


def testBuildModel_whenProviderIsUnknown_shouldRaiseModelConfigurationError() -> None:
    with pytest.raises(errors.ModelConfigurationError, match="No Provider found"):
        factory.build_model("unknownprovider/some-model", "k")


def testBuildModel_whenProviderIsUnknown_shouldStillRaiseAValueError() -> None:
    """Agents catch ValueError around model construction today."""
    with pytest.raises(ValueError):
        factory.build_model("unknownprovider/some-model", "k")


@pytest.mark.parametrize("credential", [None, "", "   "])
def testBuildModel_whenCredentialMissing_shouldRaise(credential: str | None) -> None:
    with pytest.raises(errors.ModelConfigurationError, match="API key must be set"):
        factory.build_model("openai/gpt-5.2", credential)


@pytest.mark.parametrize(
    "identifier",
    ["openai", "openai/", "/gpt-5.2", "", "openai/   ", "   /gpt-5.2", "openai//"],
)
def testParseIdentifier_whenMalformed_shouldRaise(identifier: str) -> None:
    with pytest.raises(errors.ModelConfigurationError, match="provider/model"):
        factory.parse_identifier(identifier)


def testParseIdentifier_whenModelNameHasSlashes_shouldSplitOnFirstSlashOnly() -> None:
    assert factory.parse_identifier("openrouter/moonshotai/kimi-k2.6") == (
        "openrouter",
        "moonshotai/kimi-k2.6",
    )


def testParseIdentifier_whenAliasUsed_shouldReturnCanonicalProvider() -> None:
    assert factory.parse_identifier("gemini/gemini-3.7-flash")[0] == "google"


def testBuildModel_whenNoSettingsGiven_shouldApplyDefaultSettings() -> None:
    model = factory.build_model("anthropic/claude-sonnet-4-6", "k")

    assert model.settings is not None
    assert model.settings.get("thinking") == "high"
    assert model.settings.get("timeout") == settings.DEFAULT_TIMEOUT_SECONDS


def testBuildModel_whenSettingsGiven_shouldUseThem() -> None:
    model = factory.build_model(
        "anthropic/claude-sonnet-4-6",
        "k",
        settings=settings.default_settings(max_tokens=4096, thinking="low"),
    )

    assert model.settings is not None
    assert model.settings.get("max_tokens") == 4096
    assert model.settings.get("thinking") == "low"


def testBuildModel_whenVertexEndpoint_shouldPassOptionsToTheBuilder(
    fake_service_account_info: dict[str, str],
) -> None:
    model = factory.build_model(
        "google_vertex_endpoint/glm-5_2-fp8",
        json.dumps(fake_service_account_info),
        options=options.ProviderOptions(
            vertex_endpoint_url=conftest.VERTEX_ENDPOINT_URL
        ),
    )

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert str(model.client.base_url) == f"{conftest.VERTEX_ENDPOINT_URL}/"


def testParseIdentifier_whenPartsHaveSurroundingSpaces_shouldStripThem() -> None:
    assert factory.parse_identifier(" openai / gpt-5.2 ") == ("openai", "gpt-5.2")
