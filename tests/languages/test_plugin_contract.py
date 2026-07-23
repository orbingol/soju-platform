# SPDX-License-Identifier: BSD-3-Clause
"""LanguagePlugin contract and resolver tests."""

from __future__ import annotations

import pytest

from soju.languages.contracts import LanguagePlugin
from soju.languages.korean.plugin import KoreanLanguage
from soju.languages.plugins import ENV_LANGUAGE, get_language


def test_get_language_ko_is_language_plugin() -> None:
    lang = get_language("ko")
    assert isinstance(lang, LanguagePlugin)
    assert isinstance(lang, KoreanLanguage)
    assert lang.code == "ko"
    assert lang.name == "Korean"


def test_get_language_default_is_ko(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_LANGUAGE, raising=False)
    assert get_language().code == "ko"


def test_get_language_respects_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_LANGUAGE, "ko")
    assert get_language().code == "ko"


def test_get_language_unknown_raises() -> None:
    with pytest.raises(KeyError, match="Unknown language"):
        get_language("xx")


def test_normalize_and_script_detection() -> None:
    lang = get_language("ko")
    assert lang.normalize("  밥  ") == "밥"
    assert lang.is_target_script("안녕하세요")
    assert not lang.is_target_script("hello")


def test_romanize_via_plugin() -> None:
    assert get_language("ko").romanize("학교") == "hak-gyo"


def test_conjugate_via_plugin() -> None:
    forms = get_language("ko").conjugate("먹다")
    assert forms["present"]["casual_polite"] == "먹어요"


def test_translation_system_prompt_via_plugin() -> None:
    from soju.levels import get_language_level

    level = get_language_level("1A")
    prompt = get_language("ko").translation_system_prompt(level, "vocab here")
    assert "Korean language lexicographer" in prompt
    assert level.label in prompt
    assert "vocab here" in prompt
