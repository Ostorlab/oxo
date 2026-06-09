"""Unit test for KB resolution."""

import json
import pathlib

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


def testkbGetAttribute_whenRecommendationFileMissing_returnsEntryWithEmptyRecommendation(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``recommendation.md`` is optional; the entry should resolve regardless."""
    entry_dir = tmp_path / kb.KB_FOLDER / "FAKE_ENTRY_NO_RECOMMENDATION"
    entry_dir.mkdir(parents=True)
    (entry_dir / kb.META_JSON).write_text(
        json.dumps(
            {
                "title": "Fake",
                "risk_rating": "secure",
                "short_description": "fake",
                "references": {},
            }
        ),
        encoding="utf-8",
    )
    (entry_dir / kb.DESCRIPTION).write_text("fake description", encoding="utf-8")
    monkeypatch.setattr(kb, "__file__", str(tmp_path / "kb.py"))

    entry = kb.KB.FAKE_ENTRY_NO_RECOMMENDATION

    assert entry.title == "Fake"
    assert entry.description == "fake description"
    assert entry.recommendation == ""
