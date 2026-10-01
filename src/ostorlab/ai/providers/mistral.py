"""Mistral provider."""

from __future__ import annotations

from pydantic_ai import models

from ostorlab.ai import errors
from ostorlab.ai.providers import base

# mistralai is only needed for ``mistral/...`` models: without it, every other
# provider must still import and build.
try:
    from pydantic_ai.models import mistral
    from pydantic_ai.providers import mistral as mistral_provider
except ImportError:
    mistral = None  # type: ignore[assignment]
    mistral_provider = None  # type: ignore[assignment]


def build_mistral(request: base.BuildRequest) -> models.Model:
    """Build a Mistral model."""
    if mistral is None or mistral_provider is None:
        raise errors.ModelConfigurationError(
            "The mistral provider needs the `mistralai` package: "
            "pip install 'ostorlab[agent]'"
        )
    return mistral.MistralModel(
        model_name=request.model_name,
        provider=mistral_provider.MistralProvider(api_key=request.credential),
        settings=request.settings,
    )
