# SPDX-License-Identifier: BSD-3-Clause
"""Pure fill_examples helpers (no Ollama)."""

from __future__ import annotations

from soju.fill_examples import (
    clean_example,
    form_in_sentence,
    is_bad_english,
    parse_json_content,
    validate_noun_examples,
)


def test_form_in_sentence_accepts_hada_split() -> None:
    assert form_in_sentence("샤워해요", "오늘 샤워해요.") is True


def test_clean_example_rejects_missing_fields() -> None:
    assert clean_example({}) is None
    assert clean_example({"hangul": "책"}) is None
    cleaned = clean_example({"hangul": "책이 있어요.", "english": "There is a book."})
    assert cleaned is not None
    assert cleaned["hangul"] == "책이 있어요."


def test_is_bad_english_broken_past() -> None:
    assert is_bad_english("I eated rice.", tense="past") is True
    assert is_bad_english("I ate rice.", tense="past") is False


def test_parse_json_content_strips_fences() -> None:
    raw = '```json\n{"records": []}\n```'
    parsed = parse_json_content(raw)
    assert parsed == {"records": []}


def test_validate_noun_examples_requires_hangul_in_sentence() -> None:
    assert (
        validate_noun_examples(
            [{"hangul": "좋아요.", "english": "It is good."}],
            "책",
            examples_per=1,
        )
        is None
    )
    cleaned = validate_noun_examples(
        [{"hangul": "책이 있어요.", "english": "There is a book."}],
        "책",
        examples_per=1,
    )
    assert cleaned is not None
    assert len(cleaned) == 1
