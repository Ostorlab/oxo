import pytest

from ostorlab.agent.kb import kb


def testkbGetAttribute_whenMappingExists_returnsEntry():
    entry = kb.KB.WEB_XSS

    assert entry.title is not None
    assert entry.risk_rating is not None
    assert entry.short_description is not None
    assert entry.description is not None
    assert entry.recommendation is not None


def testkbGetAttribute_whenMappingDoNotExists_raisesValueError():
    with pytest.raises(ValueError):
        kb.KB.RANDOM_FAKE_KEY

