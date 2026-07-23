# SPDX-License-Identifier: BSD-3-Clause
"""BaseLanguage contract and resolver tests."""

from __future__ import annotations

import pytest

from soju.base.contract import BaseLanguage
from soju.base.plugins import get_base_language
from soju.base.english.plugin import EnglishBase
from soju.base.plugins import ENV_BASE_LANGUAGE


def test_get_base_language_en_is_base_language() -> None:
    bl = get_base_language("en")
    assert isinstance(bl, BaseLanguage)
    assert isinstance(bl, EnglishBase)
    assert bl.code == "en"
    assert bl.name == "English"


def test_get_base_language_default_is_en(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_BASE_LANGUAGE, raising=False)
    assert get_base_language().code == "en"


def test_get_base_language_respects_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_BASE_LANGUAGE, "en")
    assert get_base_language().code == "en"


def test_get_base_language_unknown_raises() -> None:
    with pytest.raises(KeyError, match="Unknown base language"):
        get_base_language("xx")


def test_normalize_delegates_to_english_text() -> None:
    bl = get_base_language("en")
    assert bl.normalize("  a   book  ") == "a book"


def test_normalize_gloss_restores_proper_names() -> None:
    bl = get_base_language("en")
    assert bl.normalize_gloss("  South Korea  ") == "South Korea"
