"""Parsing helpers for the JSON credentials some providers take."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from ostorlab.ai import errors


def parse_json_object(
    raw_credential: str, provider_label: str, model: str
) -> dict[str, Any]:
    """Parse a JSON credential and confirm it is an object.

    Args:
        raw_credential: The credential string.
        provider_label: Human-readable provider name used in error messages.
        model: The model name, used in error messages.

    Returns:
        The parsed credential object.

    Raises:
        ModelConfigurationError: If the credential is not a JSON object.
    """
    try:
        creds = json.loads(raw_credential)
    except json.JSONDecodeError as exc:
        raise errors.ModelConfigurationError(
            f"Invalid JSON in API key for {provider_label} (model={model})."
        ) from exc
    # ``not isinstance`` rather than ``is False`` so mypy narrows ``creds`` to a dict.
    if not isinstance(creds, dict):
        raise errors.ModelConfigurationError(
            f"Credentials for {provider_label} must be a JSON object (model={model})."
        )
    return creds


def require_keys(
    creds: dict[str, Any], keys: Sequence[str], provider_label: str
) -> None:
    """Raise if any of ``keys`` is missing from the credential object."""
    missing = [key for key in keys if key not in creds]
    if len(missing) > 0:
        raise errors.ModelConfigurationError(
            f"Missing required credential(s) for {provider_label}: {', '.join(missing)}"
        )


def require_non_empty_strings(
    creds: dict[str, Any], keys: Sequence[str], provider_label: str
) -> None:
    """Raise if any of ``keys`` is present but not a non-empty string.

    Keeps a wrongly-typed field from failing later inside the provider SDK with an
    unrelated error. Absent keys are left to ``require_keys``.
    """
    invalid = [
        key
        for key in keys
        if key in creds
        and (isinstance(creds[key], str) is False or creds[key].strip() == "")
    ]
    if len(invalid) > 0:
        raise errors.ModelConfigurationError(
            f"Credential(s) for {provider_label} must be non-empty strings: "
            f"{', '.join(invalid)}"
        )
