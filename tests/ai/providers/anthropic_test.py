"""Unit tests for ostorlab.ai.providers.anthropic."""

from __future__ import annotations

import anthropic
import httpx
from pydantic_ai.models import anthropic as pydantic_anthropic

from ostorlab.ai import factory
from ostorlab.ai import options


def testBuildModel_whenAnthropic_shouldUseTheKey() -> None:
    model = factory.build_model("anthropic/claude-sonnet-4-6", "a-key")

    assert isinstance(model, pydantic_anthropic.AnthropicModel)
    assert isinstance(model.client, anthropic.AsyncAnthropic)
    assert model.client.api_key == "a-key"


def testBuildModel_whenAnthropicHttpTimeoutConfigured_shouldApplyItToTheClient() -> (
    None
):
    model = factory.build_model(
        "anthropic/claude-sonnet-4-6",
        "k",
        options=options.ProviderOptions(http_timeouts={"anthropic": httpx.Timeout(61)}),
    )

    assert isinstance(model, pydantic_anthropic.AnthropicModel)
    assert isinstance(model.client.timeout, anthropic.Timeout)
    assert model.client.timeout.read == 61
