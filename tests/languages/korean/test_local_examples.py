# SPDX-License-Identifier: BSD-3-Clause
"""Local Korean example generators (no Ollama)."""

from __future__ import annotations

from soju.languages.korean.local_examples import examples_for_noun, examples_for_verb
from soju.levels import get_language_level


def test_examples_for_noun_returns_requested_count() -> None:
    level = get_language_level("1A")
    examples = examples_for_noun(
        {"hangul": "학교", "english": "school"},
        level=level,
        examples_per=2,
    )
    assert 1 <= len(examples) <= 2
    assert all("학교" in ex["hangul"] for ex in examples)
    assert all(ex["english"] for ex in examples)


def test_examples_for_verb_covers_tenses() -> None:
    level = get_language_level("1A")
    forms = {
        "present": {"casual_polite": "먹어요", "formal_polite": "먹습니다"},
        "past": {"casual_polite": "먹었어요", "formal_polite": "먹었습니다"},
        "future": {"casual_polite": "먹을 거예요", "formal_polite": "먹겠습니다"},
    }
    result = examples_for_verb(
        {"hangul": "먹다", "english": "to eat"},
        forms,
        level=level,
        examples_per=1,
    )
    assert set(result) == {"present", "past", "future"}
    for tense in result:
        assert "casual_polite" in result[tense]
        assert result[tense]["casual_polite"][0]["hangul"]
        assert result[tense]["casual_polite"][0]["english"]
