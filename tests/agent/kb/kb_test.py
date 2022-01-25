"""Unit test for KB resolution."""
import pytest

from ostorlab.agent.kb import kb


def testkbGetAttribute_whenMappingExists_returnsEntry():
    """Test KB resolves correctly and returns a valid entry."""
    entry = kb.KB.WEB_XSS

    assert entry.title is not None
    assert entry.risk_rating is not None
    assert entry.short_description is not None
    assert entry.description is not None
    assert entry.recommendation is not None


def testkbGetAttribute_whenMappingDoNotExists_raisesValueError():
    """Test KB resolution fails with a `ValueError`."""
    with pytest.raises(ValueError):
        _ = kb.KB.RANDOM_FAKE_KEY
