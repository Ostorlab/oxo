"""Mistral provider."""

from __future__ import annotations

from pydantic_ai import models
from pydantic_ai.models import mistral
from pydantic_ai.providers import mistral as mistral_provider

from ostorlab.ai.providers import base


def build_mistral(request: base.BuildRequest) -> models.Model:
    """Build a Mistral model."""
    return mistral.MistralModel(
        model_name=request.model_name,
        provider=mistral_provider.MistralProvider(api_key=request.credential),
        settings=request.settings,
    )
