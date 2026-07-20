# SPDX-License-Identifier: BSD-3-Clause
"""Revised Romanization helper used when importing staging vocabulary."""

from __future__ import annotations

from soju.languages.korean.romanize import romanize_hangul


def test_romanize_common_dictionary_forms() -> None:
    assert romanize_hangul("학교") == "hak-gyo"
    assert romanize_hangul("먹다") == "meok-da"
    assert romanize_hangul("가다") == "ga-da"
    assert romanize_hangul("물") == "mul"
    assert romanize_hangul("책") == "chaek"
    assert romanize_hangul("커피") == "keo-pi"


def test_romanize_preserves_spaces_between_words() -> None:
    assert romanize_hangul("물을 마시다") == "mul-eul ma-si-da"


def test_romanize_compound_batchim() -> None:
    assert romanize_hangul("읽다") == "ilk-da"
    assert romanize_hangul("많다") == "manh-da"


def test_romanize_empty_and_whitespace() -> None:
    assert romanize_hangul("") == ""
    assert romanize_hangul("   ") == ""
