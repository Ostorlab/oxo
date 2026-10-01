"""Unit tests for ostorlab.ai.options."""

from __future__ import annotations

import dataclasses

import pytest

from ostorlab.ai import options


def testProviderOptions_whenNoArguments_shouldLeaveEveryOptionUnset() -> None:
    provider_options = options.ProviderOptions()

    assert provider_options.litellm_gateway_url is None
    assert provider_options.vertex_endpoint_url is None
    assert provider_options.ollama_base_url is None
    assert provider_options.qwen_base_url is None


def testProviderOptions_whenModified_shouldRaiseBecauseItIsShared() -> None:
    """One options object is shared by every model an agent builds."""
    provider_options = options.ProviderOptions(litellm_gateway_url="https://a")

    with pytest.raises(dataclasses.FrozenInstanceError):
        provider_options.litellm_gateway_url = "https://b"  # type: ignore[misc]
