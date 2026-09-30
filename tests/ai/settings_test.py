"""Unit tests for ostorlab.ai.settings."""

from __future__ import annotations

import pydantic_ai
import pytest
from pytest_httpx import HTTPXMock

from ostorlab.ai import factory
from ostorlab.ai import settings

_CHAT_COMPLETION = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 0,
    "model": "deepseek-chat",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "ok"},
            "finish_reason": "stop",
        }
    ],
}


def testDefaultSettings_whenNoArguments_shouldUseHighThinkingAndLongTimeout() -> None:
    model_settings = settings.default_settings()

    assert model_settings == {"timeout": 1800, "thinking": "high"}


def testDefaultSettings_whenMaxTokensGiven_shouldSetIt() -> None:
    assert settings.default_settings(max_tokens=8192).get("max_tokens") == 8192


@pytest.mark.parametrize("timeout", [None, 42])
def testDefaultSettings_whenModelRuns_shouldSendTheTimeoutWithTheRequest(
    httpx_mock: HTTPXMock, timeout: int | None
) -> None:
    """The settings timeout is what bounds a request: pydantic-ai sends it per request."""
    httpx_mock.add_response(
        url="https://api.deepseek.com/chat/completions", json=_CHAT_COMPLETION
    )
    model_settings = (
        settings.default_settings()
        if timeout is None
        else settings.default_settings(timeout=timeout)
    )
    model = factory.build_model("deepseek/deepseek-chat", "k", settings=model_settings)

    pydantic_ai.Agent(model).run_sync("hello")

    request = httpx_mock.get_request()
    assert request is not None
    expected = settings.DEFAULT_TIMEOUT_SECONDS if timeout is None else timeout
    assert request.extensions["timeout"]["read"] == expected
    assert request.extensions["timeout"]["connect"] == expected
