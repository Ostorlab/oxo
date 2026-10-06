"""Unit tests for the ostorlab.ai package import guard."""

from __future__ import annotations

import importlib
import sys

import pytest


def testImportOstorlabAi_whenAgentExtraMissing_shouldExplainHowToInstallIt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``None`` entry in ``sys.modules`` makes ``import pydantic_ai`` fail."""
    monkeypatch.setitem(sys.modules, "pydantic_ai", None)
    monkeypatch.delitem(sys.modules, "ostorlab.ai")

    with pytest.raises(ImportError, match=r"pip install 'ostorlab\[agent\]'"):
        importlib.import_module("ostorlab.ai")
