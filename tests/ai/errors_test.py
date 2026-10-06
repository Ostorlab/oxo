"""Unit tests for ostorlab.ai.errors."""

from __future__ import annotations

import pytest

from ostorlab import exceptions
from ostorlab.ai import errors


@pytest.mark.parametrize(
    "base_class", [errors.Error, exceptions.OstorlabError, ValueError]
)
def testModelConfigurationError_whenRaised_shouldBeCaughtByEveryBaseClass(
    base_class: type[Exception],
) -> None:
    """Agents catch ValueError today; oxo code catches OstorlabError."""
    with pytest.raises(base_class):
        raise errors.ModelConfigurationError("bad configuration")
