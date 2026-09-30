"""xAI provider (gRPC, so HTTP timeouts do not apply)."""

from __future__ import annotations

from pydantic_ai import models
from pydantic_ai.models import xai
from pydantic_ai.providers import xai as xai_provider

from ostorlab.ai.providers import base


def build_xai(request: base.BuildRequest) -> models.Model:
    """Build an xAI (Grok) model."""
    return xai.XaiModel(
        model_name=request.model_name,
        provider=xai_provider.XaiProvider(api_key=request.credential),
        settings=request.settings,
    )
