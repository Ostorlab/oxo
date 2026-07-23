"""Unit test for KB resolution."""

import pytest

from ostorlab.agent.kb import kb


def testkbGetAttribute_whenMappingExists_returnsEntry() -> None:
    """Test KB resolves correctly and returns a valid entry."""
    entry = kb.KB.WEB_XSS

    assert entry.title is not None
    assert entry.risk_rating is not None
    assert entry.short_description is not None
    assert entry.description is not None
    assert entry.recommendation is not None


def testkbGetAttribute_whenMappingDoNotExists_raisesValueError() -> None:
    """Test KB resolution fails with a `ValueError`."""
    with pytest.raises(ValueError):
        _ = kb.KB.RANDOM_FAKE_KEY


def testkbGetAttribute_whenStagingDevHostnamesEntry_returnsEntry() -> None:
    """Regression guard that the staging/dev hostnames KB entry resolves.

    A future submodule bump that accidentally targets a commit without this
    entry would otherwise go undetected until runtime, because the generic
    ``WEB_XSS`` / fake-key tests still pass without it.
    """
    entry = kb.KB.APK_STAGING_DEV_HOSTNAMES_IN_RELEASE

    assert entry.title is not None
    assert entry.risk_rating is not None
    assert entry.references is not None
