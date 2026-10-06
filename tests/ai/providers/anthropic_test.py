"""Unit tests for ostorlab.ai.providers.anthropic."""

from __future__ import annotations

import anthropic
from pydantic_ai.models import anthropic as pydantic_anthropic

from ostorlab.ai import factory


def testBuildModel_whenAnthropic_shouldUseTheKey() -> None:
    model = factory.build_model("anthropic/claude-sonnet-4-6", "a-key")

    assert isinstance(model, pydantic_anthropic.AnthropicModel)
    assert isinstance(model.client, anthropic.AsyncAnthropic)
    assert model.client.api_key == "a-key"
