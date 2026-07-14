# SPDX-License-Identifier: BSD-3-Clause
"""translate_words parsers (no Ollama)."""

from __future__ import annotations

from soju.translate_words import normalize_record, parse_word_list_lines, strip_bullet


def test_parse_word_list_arrow_and_bullet() -> None:
    hints = parse_word_list_lines(["* 학교 -> school", "친구"])
    assert len(hints) == 2
    assert hints[0].entry == "학교"
    assert hints[0].hint_english == "school"
    assert hints[1].entry == "친구"


def test_normalize_record_requires_fields() -> None:
    assert normalize_record({"hangul": "책"}) is None
    record = normalize_record(
        {
            "hangul": "책",
            "romanization": "Chaek",
            "english": "book",
            "type": "noun",
        }
    )
    assert record is not None
    assert record["hangul"] == "책"
    assert record["romanization"] == "chaek"
    assert record["english"] == "book"


def test_strip_bullet() -> None:
    assert strip_bullet("- foo") == "foo"
    assert strip_bullet("* bar") == "bar"
