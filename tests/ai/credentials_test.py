"""Unit tests for ostorlab.ai.credentials."""

from __future__ import annotations

import pytest

from ostorlab.ai import credentials
from ostorlab.ai import errors


def testParseJsonObject_whenValidObject_shouldReturnIt() -> None:
    assert credentials.parse_json_object('{"a": 1}', "X provider", "m") == {"a": 1}


@pytest.mark.parametrize(
    ("raw", "message"),
    [("{bad", "Invalid JSON"), ("[1]", "must be a JSON object")],
)
def testParseJsonObject_whenNotAJsonObject_shouldRaise(raw: str, message: str) -> None:
    with pytest.raises(errors.ModelConfigurationError, match=message):
        credentials.parse_json_object(raw, "X provider", "m")


def testParseJsonObject_whenInvalid_shouldNotLeakTheCredentialInTheMessage() -> None:
    with pytest.raises(errors.ModelConfigurationError) as exc_info:
        credentials.parse_json_object("{super-secret", "X provider", "m")

    assert "super-secret" not in str(exc_info.value)


def testRequireKeys_whenKeysMissing_shouldListThem() -> None:
    with pytest.raises(errors.ModelConfigurationError, match="b, c"):
        credentials.require_keys({"a": 1}, ["a", "b", "c"], "X provider")
