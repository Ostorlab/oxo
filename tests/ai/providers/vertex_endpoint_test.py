"""Unit tests for ostorlab.ai.providers.vertex_endpoint."""

from __future__ import annotations

import json
import typing

import pytest
from google.oauth2 import service_account
from pydantic_ai.models import openai as pydantic_openai
from pydantic_ai.profiles import openai as openai_profile

from ostorlab.ai import errors
from ostorlab.ai import factory
from ostorlab.ai import options
from ostorlab.ai.providers import vertex_endpoint
from tests.ai import conftest

_MODEL = "google_vertex_endpoint/glm-5_2-fp8"
_OPTIONS = options.ProviderOptions(vertex_endpoint_url=conftest.VERTEX_ENDPOINT_URL)


def testBuildModel_whenVertexEndpoint_shouldBuildOpenAIModelTargetingEndpoint(
    fake_service_account_info: dict[str, str],
) -> None:
    model = factory.build_model(
        _MODEL, json.dumps(fake_service_account_info), options=_OPTIONS
    )

    assert isinstance(model, pydantic_openai.OpenAIChatModel)
    assert model.model_name == "glm-5_2-fp8"
    assert str(model.client.base_url) == f"{conftest.VERTEX_ENDPOINT_URL}/"
    assert model.client.api_key == "fake-access-token"


def testBuildModel_whenVertexEndpoint_shouldSupportToolChoiceRequired(
    fake_service_account_info: dict[str, str],
) -> None:
    model = factory.build_model(
        _MODEL, json.dumps(fake_service_account_info), options=_OPTIONS
    )

    assert isinstance(model.profile, openai_profile.OpenAIModelProfile)
    assert model.profile.openai_supports_tool_choice_required is True
    assert model.profile.openai_chat_thinking_field == "reasoning_content"


@pytest.mark.parametrize(
    ("url", "message"),
    [
        (None, "must be set"),
        ("   ", "must be set"),
        (f"{conftest.VERTEX_ENDPOINT_URL}/", "trailing slash"),
        ("ftp://example.com", "must start with"),
    ],
)
def testBuildModel_whenVertexEndpointUrlInvalid_shouldRaise(
    fake_service_account_info: dict[str, str], url: str | None, message: str
) -> None:
    with pytest.raises(errors.ModelConfigurationError, match=message):
        factory.build_model(
            _MODEL,
            json.dumps(fake_service_account_info),
            options=options.ProviderOptions(vertex_endpoint_url=url),
        )


@pytest.mark.parametrize(
    ("credential", "message"),
    [
        ("not-json", "Invalid JSON"),
        ("{}", "service account credentials"),
        (
            json.dumps({"type": "service_account", "project_id": "p"}),
            "service account credentials",
        ),
    ],
)
def testBuildModel_whenVertexEndpointServiceAccountInvalid_shouldRaise(
    credential: str, message: str
) -> None:
    with pytest.raises(errors.ModelConfigurationError, match=message):
        factory.build_model(_MODEL, credential, options=_OPTIONS)


def testVertexEndpointModelRefresh_whenCalled_shouldBuildIndependentSiblingModel(
    fake_service_account_info: dict[str, str],
) -> None:
    """Each refresh() must return a new model with its own loop-bound httpx client."""
    model = factory.build_model(
        _MODEL, json.dumps(fake_service_account_info), options=_OPTIONS
    )
    assert isinstance(model, vertex_endpoint.VertexEndpointModel)

    refreshed = model.refresh()

    assert isinstance(refreshed, vertex_endpoint.VertexEndpointModel)
    assert refreshed is not model
    assert refreshed.client is not model.client
    assert refreshed.model_name == model.model_name
    assert str(refreshed.client.base_url) == str(model.client.base_url)


def testGetTokenProvider_whenCalledTwiceForSameCredential_shouldReturnSameInstance(
    fake_service_account_info: dict[str, str],
) -> None:
    payload = json.dumps(fake_service_account_info)

    assert vertex_endpoint.get_token_provider(
        payload
    ) is vertex_endpoint.get_token_provider(payload)


def testTokenProvider_whenTokenIsMissing_shouldMintOneAndReturnIt(
    stub_vertex_credentials: typing.Callable[[bool], conftest.StubVertexCredentials],
) -> None:
    credentials = stub_vertex_credentials(False)
    token_provider = vertex_endpoint.VertexEndpointTokenProvider(
        typing.cast(service_account.Credentials, credentials)
    )

    token = token_provider.bearer_token

    assert credentials.refresh_count == 1
    assert token == "refreshed-token-1"


def testTokenProvider_whenTokenIsStillValid_shouldReuseItWithoutRefreshing(
    stub_vertex_credentials: typing.Callable[[bool], conftest.StubVertexCredentials],
) -> None:
    credentials = stub_vertex_credentials(True)
    token_provider = vertex_endpoint.VertexEndpointTokenProvider(
        typing.cast(service_account.Credentials, credentials)
    )

    token = token_provider.bearer_token

    assert credentials.refresh_count == 0
    assert token == "initial-token"


def testTokenProvider_whenTokenExpiresBetweenRequests_shouldRefreshOnceMore(
    stub_vertex_credentials: typing.Callable[[bool], conftest.StubVertexCredentials],
) -> None:
    credentials = stub_vertex_credentials(False)
    token_provider = vertex_endpoint.VertexEndpointTokenProvider(
        typing.cast(service_account.Credentials, credentials)
    )

    first_token = token_provider.bearer_token
    second_token = token_provider.bearer_token
    credentials.valid = False
    third_token = token_provider.bearer_token

    assert credentials.refresh_count == 2
    assert (first_token, second_token, third_token) == (
        "refreshed-token-1",
        "refreshed-token-1",
        "refreshed-token-2",
    )


def testTokenProvider_whenRefreshYieldsNoToken_shouldRaise(
    stub_vertex_credentials: typing.Callable[[bool], conftest.StubVertexCredentials],
) -> None:
    """A None token would otherwise be sent as the literal string "Bearer None"."""
    credentials = stub_vertex_credentials(True)
    credentials.token = None
    token_provider = vertex_endpoint.VertexEndpointTokenProvider(
        typing.cast(service_account.Credentials, credentials)
    )

    with pytest.raises(errors.ModelConfigurationError, match="no access token"):
        _ = token_provider.bearer_token
