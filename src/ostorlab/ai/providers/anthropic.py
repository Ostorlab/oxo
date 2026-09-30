"""Anthropic provider."""

from __future__ import annotations

from pydantic_ai import models
from pydantic_ai.models import anthropic
from pydantic_ai.providers import anthropic as anthropic_provider

from ostorlab.ai.providers import base


def build_anthropic(request: base.BuildRequest) -> models.Model:
    """Build an Anthropic model."""
    return anthropic.AnthropicModel(
        model_name=request.model_name,
        provider=anthropic_provider.AnthropicProvider(
            api_key=request.credential,
        ),
        settings=request.settings,
    )
