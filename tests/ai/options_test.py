"""Unit tests for ostorlab.ai.options."""

from __future__ import annotations

import httpx

from ostorlab.ai import options


def testHttpClientFor_whenTimeoutConfigured_shouldBuildClientWithThatTimeout() -> None:
    provider_options = options.ProviderOptions(
        http_timeouts={"google": httpx.Timeout(250, connect=5)}
    )

    http_client = provider_options.http_client_for("google")

    assert http_client is not None
    assert http_client.timeout == httpx.Timeout(250, connect=5)


def testHttpClientFor_whenProviderHasNoTimeout_shouldReturnNone() -> None:
    provider_options = options.ProviderOptions(http_timeouts={"google": 250})

    assert provider_options.http_client_for("openai") is None


def testHttpClientFor_whenCalledTwice_shouldReturnDistinctClients() -> None:
    """Each model gets its own client, bound to the event loop that uses it."""
    provider_options = options.ProviderOptions(http_timeouts={"google": 250})

    assert provider_options.http_client_for(
        "google"
    ) is not provider_options.http_client_for("google")
