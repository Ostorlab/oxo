"""Types shared by every provider builder."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable

from pydantic_ai import models
from pydantic_ai import settings as pydantic_ai_settings
from pydantic_ai.profiles import openai as openai_profile

from ostorlab.ai import options as options_module


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class BuildRequest:
    """Everything a builder needs to construct one model.

    Attributes:
        provider: Canonical provider name (aliases already resolved).
        model_name: Model name as the provider expects it.
        credential: The provider secret: a plain API key, or a JSON object for
            providers that need several fields (Bedrock, Azure, Vertex).
        options: Deployment-wide provider options.
        settings: pydantic-ai settings applied to the model.
    """

    provider: str
    model_name: str
    credential: str
    options: options_module.ProviderOptions
    settings: pydantic_ai_settings.ModelSettings


Builder = Callable[[BuildRequest], models.Model]


def reasoning_content_profile(
    supports_tool_choice_required: bool = False,
) -> openai_profile.OpenAIModelProfile:
    """Profile for OpenAI-compatible gateways exposing reasoning as ``reasoning_content``.

    Safe for non-thinking models: they never emit the field, so it stays inert and
    pydantic-ai never sends thinking parts back.
    """
    return openai_profile.OpenAIModelProfile(
        openai_supports_tool_choice_required=supports_tool_choice_required,
        openai_chat_thinking_field="reasoning_content",
        openai_chat_send_back_thinking_parts="field",
    )
