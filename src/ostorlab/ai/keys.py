"""Helpers for agents that configure one credential per provider.

Agents such as azrael or threat_intelligence read ``OPENROUTER_API_KEY``,
``ANTHROPIC_API_KEY``, ... and pick the key matching the configured model's
provider. They pass those keys here as a mapping keyed by provider name.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from ostorlab.ai import factory

# Order in which a configured credential is picked when the agent has no explicit
# model provider, e.g. to forward one key to a sub-process.
PROVIDER_PRIORITY: Final[tuple[str, ...]] = (
    "litellm",
    "openrouter",
    "z_ai",
    "xai",
    "google",
    "google_vertex",
    "google_vertex_endpoint",
    "openai",
    "deepseek",
    "moonshotai",
    "anthropic",
    "aws_bedrock",
    "azure_ai_foundry",
    "fireworks",
)


def credential_for(provider: str, keys: Mapping[str, str | None]) -> str | None:
    """Return the configured credential for ``provider``, or None if unset or blank.

    Args:
        provider: Provider name; aliases such as ``gemini`` are resolved.
        keys: Credentials keyed by canonical provider name.
    """
    credential = keys.get(factory.canonical_provider(provider))
    if credential is None or credential.strip() == "":
        return None
    return credential


def first_available(keys: Mapping[str, str | None]) -> tuple[str, str] | None:
    """Return ``(provider, credential)`` for the highest-priority configured provider."""
    for provider in PROVIDER_PRIORITY:
        credential = credential_for(provider, keys)
        if credential is not None:
            return provider, credential
    return None
