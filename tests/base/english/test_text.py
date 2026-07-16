# SPDX-License-Identifier: BSD-3-Clause
"""English gloss normalization."""

from soju.base.english.text import normalize_english, normalize_english_gloss


def test_normalize_english_collapses_whitespace() -> None:
    assert normalize_english("  a   book  ") == "a book"


def test_normalize_english_gloss_proper_names() -> None:
    assert normalize_english_gloss("south korea") == "South Korea"
    assert normalize_english_gloss("a book") == "a book"
