"""Helpers for tenacity retries."""

from typing import Any

import tenacity


def return_last_value(retry_state: tenacity.RetryCallState) -> Any:
    """Return the value of the last attempt once the retries are exhausted, instead of raising RetryError.

    `retry_state.outcome` is a Future: returning it as is gives callers an object that is always truthy and never
    `False`, so a check that kept failing would read as a success.

    Args:
        retry_state: State of the exhausted retry.

    Returns:
        The value returned by the last attempt, or None if no attempt ran.
    """
    if retry_state.outcome is None:
        return None
    return retry_state.outcome.result()
