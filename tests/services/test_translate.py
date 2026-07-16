# SPDX-License-Identifier: BSD-3-Clause
"""Translate service parsers (no Ollama)."""

from __future__ import annotations

import pytest

from soju.services.translate import (
    normalize_record,
    parse_batch_records,
    parse_word_list_lines,
    strip_bullet,
)


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


def _valid_record(hangul: str, english: str) -> dict:
    return {
        "hangul": hangul,
        "romanization": "x",
        "english": english,
        "type": "noun",
    }


def test_parse_batch_records_accepts_matching_count() -> None:
    batch = parse_word_list_lines(["학교", "친구"])
    records = parse_batch_records(
        batch,
        {"records": [_valid_record("학교", "school"), _valid_record("친구", "friend")]},
    )
    assert [r["hangul"] for r in records] == ["학교", "친구"]


def test_parse_batch_records_rejects_count_mismatch() -> None:
    batch = parse_word_list_lines(["학교", "친구"])
    with pytest.raises(ValueError, match="Expected 2 records, got 1"):
        parse_batch_records(batch, {"records": [_valid_record("학교", "school")]})


def test_parse_batch_records_rejects_invalid_record() -> None:
    batch = parse_word_list_lines(["학교"])
    with pytest.raises(ValueError, match="Record 1 is missing required fields"):
        parse_batch_records(batch, {"records": [{"hangul": "학교"}]})


def test_parse_batch_records_rejects_non_object() -> None:
    batch = parse_word_list_lines(["학교"])
    with pytest.raises(ValueError, match="Record 1 is not an object"):
        parse_batch_records(batch, {"records": ["학교"]})


class _FakeTranslateLlm:
    def chat(
        self,
        messages,
        *,
        json_mode: bool = True,
        temperature: float = 0.3,
        num_predict: int | None = None,
    ) -> str:
        return '{"records":[{"hangul":"사과","romanization":"sa-gwa","english":"apple","type":"noun"}]}'


def test_translate_words_with_fake_llm(data_root, monkeypatch) -> None:
    from soju.services.translate import translate_words

    monkeypatch.setenv("DATA_DIR", str(data_root))
    records, warnings = translate_words(
        ["사과"],
        llm=_FakeTranslateLlm(),
        batch_size=8,
        temperature=0.0,
        skip_existing=False,
        level_id="1A",
    )
    assert warnings == []
    assert records[0]["hangul"] == "사과"
    assert records[0]["english"] == "apple"
