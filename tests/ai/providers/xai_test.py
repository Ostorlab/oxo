"""Unit tests for ostorlab.ai.providers.xai."""

from __future__ import annotations

from pydantic_ai.models import xai as pydantic_xai

from ostorlab.ai import factory


def testBuildModel_whenXai_shouldBuildGrokModelWithDefaultSettings() -> None:
    model = factory.build_model("xai/grok-4.5", "x-key")

    assert isinstance(model, pydantic_xai.XaiModel)
    assert model.model_name == "grok-4.5"
    assert model.settings is not None
    assert model.settings.get("thinking") == "high"
