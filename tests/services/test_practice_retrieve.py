# SPDX-License-Identifier: BSD-3-Clause
"""Practice retrieve ranking over embedding cache fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from soju.services.embeddings.retrieve import PracticeRetrieveError, retrieve_practice


def _write_cache(tmp_path: Path, *, dimension: int = 2) -> Path:
    data = tmp_path / "data"
    cache = data / "cache" / "embeddings"
    cache.mkdir(parents=True)
    (cache / "meta.json").write_text(
        json.dumps({"embed_model": "test-embed", "dimension": dimension, "vocab_count": 2, "grammar_count": 1}),
        encoding="utf-8",
    )
    vocab = [
        {"id": "a", "hangul": "커피", "romanization": "keo-pi", "english": "coffee", "type": "noun", "level": "1A", "embedding": [1.0, 0.0]},
        {"id": "b", "hangul": "총", "romanization": "chong", "english": "gun", "type": "noun", "level": "1A", "embedding": [0.0, 1.0]},
        {"id": "c", "hangul": "여행", "romanization": "yeo-haeng", "english": "travel", "type": "noun", "level": None, "embedding": [0.7, 0.7]},
    ]
    grammar = [
        {
            "id": "hago",
            "form": "-하고",
            "english": "and / with",
            "category": "particle",
            "summary": "Connect nouns.",
            "level": "1A",
            "embedding": [1.0, 0.0],
        }
    ]
    (cache / "vocab.jsonl").write_text("\n".join(json.dumps(row) for row in vocab) + "\n", encoding="utf-8")
    (cache / "grammar.jsonl").write_text("\n".join(json.dumps(row) for row in grammar) + "\n", encoding="utf-8")

    levels = data / "content"
    levels.mkdir(parents=True)
    (levels / "levels.yaml").write_text(
        "default: 1A\nlevels:\n  1A:\n    label: Korean 1A\n    description: Beginner\n    guidance: Keep it simple.\n",
        encoding="utf-8",
    )
    return data


def test_retrieve_practice_ranks_by_cosine(tmp_path: Path) -> None:
    data = _write_cache(tmp_path)
    result = retrieve_practice(query_vector=[1.0, 0.0], level="1A", vocab_k=1, grammar_m=1, root=data)
    assert result.hangul == ["커피"]
    assert result.grammar[0].form == "-하고"
    assert result.grammar[0].summary == "Connect nouns."


def test_retrieve_practice_include_unassigned(tmp_path: Path) -> None:
    data = _write_cache(tmp_path)
    without = retrieve_practice(query_vector=[0.7, 0.7], level="1A", vocab_k=3, root=data, include_unassigned=False)
    with_extra = retrieve_practice(query_vector=[0.7, 0.7], level="1A", vocab_k=3, root=data, include_unassigned=True)
    assert "여행" not in without.hangul
    assert "여행" in with_extra.hangul


def test_retrieve_practice_missing_cache(tmp_path: Path) -> None:
    with pytest.raises(PracticeRetrieveError) as exc:
        retrieve_practice(query_vector=[1.0], level="1A", root=tmp_path / "empty")
    assert exc.value.status == 503


def test_screen_blocklist() -> None:
    from soju.backend.services.practice_prompts import (
        PracticeTopicBlockedError,
        build_practice_system_prompt,
        build_story_topic_prompt,
        screen_practice_text,
    )

    with pytest.raises(PracticeTopicBlockedError):
        screen_practice_text("a story about guns and fighting")

    prompt = build_practice_system_prompt(
        level_label="Korean 1A",
        level_guidance="Keep it simple.",
        grammar_summary=None,
        theme_text="Café",
        exercise_type="sentences",
        count=2,
        hangul=["커피"],
        grammar=[],
    )
    assert "under 18" in prompt.lower()
    assert "Café" in prompt

    topic_prompt = build_story_topic_prompt(
        level_label="Korean 1A",
        level_guidance="Keep it simple.",
        theme_text="Café orders",
        previous_topic="What did you drink?",
    )
    assert "FORBIDDEN" in topic_prompt
    assert "Café orders" in topic_prompt
    assert "What did you drink?" in topic_prompt
    assert "6–12 words" in topic_prompt or "6-12 words" in topic_prompt


def test_parse_story_topic_keeps_first_question_only() -> None:
    from soju.backend.services.practice_session import parse_story_topic_json

    topic = parse_story_topic_json(
        '{"topic": "What do you like to drink at a café? Practice ordering and asking about menu items."}'
    )
    assert topic == "What do you like to drink at a café?"
    assert "Practice" not in topic
