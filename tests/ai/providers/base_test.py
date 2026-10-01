"""Unit tests for ostorlab.ai.providers.base."""

from __future__ import annotations

from ostorlab.ai import options
from ostorlab.ai import settings
from ostorlab.ai.providers import base


def testReasoningContentProfile_whenBuilt_shouldReadAndSendBackReasoningContent() -> (
    None
):
    profile = base.reasoning_content_profile()

    assert profile.openai_chat_thinking_field == "reasoning_content"
    assert profile.openai_chat_send_back_thinking_parts == "field"
    assert profile.openai_supports_tool_choice_required is False


def testReasoningContentProfile_whenToolChoiceRequiredSupported_shouldEnableIt() -> (
    None
):
    profile = base.reasoning_content_profile(supports_tool_choice_required=True)

    assert profile.openai_supports_tool_choice_required is True


def testBuildRequest_whenRepresented_shouldNotExposeTheCredential() -> None:
    """Requests end up in logs, test failures and error-tracker locals."""
    request = base.BuildRequest(
        provider="openai",
        model_name="gpt-5.2",
        credential="sk-super-secret",
        options=options.ProviderOptions(),
        settings=settings.default_settings(),
    )

    assert "sk-super-secret" not in repr(request)
    assert "gpt-5.2" in repr(request)
