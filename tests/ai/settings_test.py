"""Unit tests for ostorlab.ai.settings."""

from __future__ import annotations

from ostorlab.ai import settings


def testDefaultSettings_whenNoArguments_shouldUseHighThinkingAndLongTimeout() -> None:
    model_settings = settings.default_settings()

    assert model_settings == {"timeout": 1800, "thinking": "high"}


def testDefaultSettings_whenMaxTokensGiven_shouldSetIt() -> None:
    assert settings.default_settings(max_tokens=8192).get("max_tokens") == 8192
