"""Unit tests for ostorlab.ai.providers.mistral."""

from __future__ import annotations

from pydantic_ai.models import mistral as pydantic_mistral

from ostorlab.ai import factory
from ostorlab.ai import settings


def testBuildModel_whenMistral_shouldBuildMistralModelWithTheGivenSettings() -> None:
    model = factory.build_model(
        "mistral/mistral-small-latest",
        "m-key",
        settings=settings.default_settings(max_tokens=2048),
    )

    assert isinstance(model, pydantic_mistral.MistralModel)
    assert model.model_name == "mistral-small-latest"
    assert model.system == "mistral"
    assert model.settings is not None
    assert model.settings.get("max_tokens") == 2048
