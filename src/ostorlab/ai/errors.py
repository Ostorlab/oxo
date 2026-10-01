"""Errors raised while building a model."""

from __future__ import annotations

from ostorlab import exceptions


class Error(exceptions.OstorlabError):
    """Base exception for all errors in ``ostorlab.ai``."""


class ModelConfigurationError(Error, ValueError):
    """The model identifier, credential or provider options are unusable.

    Also a ``ValueError`` so agents that already catch ``ValueError`` around model
    construction keep working unchanged.
    """
