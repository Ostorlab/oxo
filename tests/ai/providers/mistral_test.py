"""Unit tests for ostorlab.ai.providers.mistral."""

from __future__ import annotations

import pytest
from pydantic_ai.models import mistral as pydantic_mistral

from ostorlab.ai import errors
from ostorlab.ai import factory
from ostorlab.ai import settings
from ostorlab.ai.providers import mistral as mistral_module


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


def testBuildModel_whenMistralSdkMissing_shouldRaiseAndKeepOtherProvidersWorking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing optional SDK must only affect its own provider."""
    monkeypatch.setattr(mistral_module, "mistral", None)

    with pytest.raises(errors.ModelConfigurationError, match="mistralai"):
        factory.build_model("mistral/mistral-small-latest", "k")
    assert factory.build_model("anthropic/claude-sonnet-4-6", "k") is not None
