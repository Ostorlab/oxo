"""Default pydantic-ai model settings shared by every agent."""

from __future__ import annotations

from pydantic_ai import settings as pydantic_ai_settings

DEFAULT_TIMEOUT_SECONDS = 1800


def default_settings(
    max_tokens: int | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    thinking: pydantic_ai_settings.ThinkingLevel = "high",
) -> pydantic_ai_settings.ModelSettings:
    """Build the model settings every agent uses unless it overrides them.

    Args:
        max_tokens: Output token cap; omitted from the settings when None so the
            provider default applies.
        timeout: Request timeout in seconds.
        thinking: Reasoning effort requested from thinking-capable models.

    Returns:
        The pydantic-ai model settings.
    """
    model_settings = pydantic_ai_settings.ModelSettings(
        timeout=timeout,
        thinking=thinking,
    )
    if max_tokens is not None:
        model_settings["max_tokens"] = max_tokens
    return model_settings
