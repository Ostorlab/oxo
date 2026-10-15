"""Unit test for retry utils module."""

import tenacity

from ostorlab.utils import retry


def testReturnLastValue_whenRetriesExhausted_returnsLastAttemptValue() -> None:
    """A check that keeps failing must return the falsy value of its last attempt, not the truthy Future."""

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_none(),
        retry_error_callback=retry.return_last_value,
        retry=tenacity.retry_if_result(lambda v: v is False),
    )
    def is_healthy() -> bool:
        return False

    assert is_healthy() is False


def testReturnLastValue_whenNoAttemptRan_returnsNone() -> None:
    """Without any attempt there is no value to return."""
    retry_state = tenacity.RetryCallState(
        retry_object=tenacity.Retrying(), fn=None, args=(), kwargs={}
    )

    assert retry.return_last_value(retry_state) is None
