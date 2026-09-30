"""Unit tests for ostorlab.ai.keys."""

from __future__ import annotations

import pytest

from ostorlab.ai import factory
from ostorlab.ai import keys


def testCredentialFor_whenAliasUsed_shouldResolveCanonicalProviderKey() -> None:
    assert keys.credential_for("gemini", {"google": "g-key"}) == "g-key"


@pytest.mark.parametrize("value", [None, "", "  "])
def testCredentialFor_whenKeyUnsetOrBlank_shouldReturnNone(value: str | None) -> None:
    assert keys.credential_for("openai", {"openai": value}) is None


def testFirstAvailable_whenSeveralKeysSet_shouldFollowPriority() -> None:
    configured = {"anthropic": "a-key", "openrouter": "or-key", "openai": ""}

    assert keys.first_available(configured) == ("openrouter", "or-key")


def testFirstAvailable_whenNoKeySet_shouldReturnNone() -> None:
    assert keys.first_available({"openai": None}) is None


def testProviderPriority_whenCompared_shouldListEverySupportedProvider() -> None:
    assert sorted(keys.PROVIDER_PRIORITY) == sorted(factory.SUPPORTED_PROVIDERS)


def testCredentialFor_whenKeyHasSurroundingWhitespace_shouldStripIt() -> None:
    assert keys.credential_for("openai", {"openai": "  sk-key\n"}) == "sk-key"
