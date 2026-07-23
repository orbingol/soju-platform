# SPDX-License-Identifier: BSD-3-Clause
"""Language levels config loading under content/."""

from __future__ import annotations

from pathlib import Path

import yaml

from soju.levels import default_level_id, grammar_for_level, load_levels_config, vocabulary_for_level
from soju.registry.grammar import load_grammar_pattern, save_grammar_pattern
from soju.registry.vocabulary import load_vocabulary, save_vocabulary
from tests.constants import VERB_ID, WORD_ID


def test_loads_from_content_levels_yaml(data_root: Path) -> None:
    assert default_level_id(data_root) == "1A"
    config = load_levels_config(data_root)
    assert "1A" in config["levels"]


def test_missing_levels_raises(tmp_path: Path) -> None:
    try:
        default_level_id(tmp_path)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "Missing levels config" in str(exc)


def test_vocabulary_for_level_includes_tagged_entries(data_root: Path) -> None:
    entries = vocabulary_for_level("1A", data_root)
    ids = {e["id"] for e in entries}
    assert WORD_ID in ids
    assert VERB_ID in ids


def test_vocabulary_for_level_excludes_unassigned_by_default(data_root: Path) -> None:
    vocab = load_vocabulary(data_root)
    for entry in vocab:
        entry.pop("level", None)
    save_vocabulary(vocab, data_root)

    assert vocabulary_for_level("1A", data_root) == []


def test_vocabulary_for_level_include_unassigned(data_root: Path) -> None:
    vocab = load_vocabulary(data_root)
    for entry in vocab:
        if entry["id"] == WORD_ID:
            entry.pop("level", None)
        else:
            entry["level"] = "1A"
    save_vocabulary(vocab, data_root)

    without = {e["id"] for e in vocabulary_for_level("1A", data_root)}
    assert WORD_ID not in without
    assert VERB_ID in without

    with_extra = {e["id"] for e in vocabulary_for_level("1A", data_root, include_unassigned=True)}
    assert WORD_ID in with_extra
    assert VERB_ID in with_extra


def test_vocabulary_for_level_expands_include_levels(data_root: Path) -> None:
    vocab = load_vocabulary(data_root)
    for entry in vocab:
        if entry["id"] == WORD_ID:
            entry["level"] = "1A"
        elif entry["id"] == VERB_ID:
            entry["level"] = "1B"
    save_vocabulary(vocab, data_root)

    only_1a = {e["id"] for e in vocabulary_for_level("1A", data_root)}
    assert only_1a == {WORD_ID}

    at_1b = {e["id"] for e in vocabulary_for_level("1B", data_root)}
    assert at_1b == {WORD_ID, VERB_ID}


def test_vocabulary_for_level_empty_when_no_matches(data_root: Path) -> None:
    levels = data_root / "content" / "levels.yaml"
    levels.write_text(
        yaml.safe_dump(
            {
                "default": "1A",
                "levels": {
                    "1A": {"label": "1A", "guidance": "x"},
                    "2A": {"label": "2A", "guidance": "y"},
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    # Fixture vocabulary is tagged 1A only.
    assert vocabulary_for_level("2A", data_root) == []


def test_grammar_for_level_includes_tagged_patterns(data_root: Path) -> None:
    rows = grammar_for_level("1A", data_root)
    assert {r["id"] for r in rows} == {"do"}


def test_grammar_for_level_excludes_unassigned_by_default(data_root: Path) -> None:
    pattern = load_grammar_pattern("do", data_root)
    pattern.pop("level", None)
    save_grammar_pattern("do", pattern, data_root)

    assert grammar_for_level("1A", data_root) == []


def test_grammar_for_level_include_unassigned(data_root: Path) -> None:
    pattern = load_grammar_pattern("do", data_root)
    pattern.pop("level", None)
    save_grammar_pattern("do", pattern, data_root)

    assert grammar_for_level("1A", data_root) == []
    with_extra = grammar_for_level("1A", data_root, include_unassigned=True)
    assert [r["id"] for r in with_extra] == ["do"]


def test_grammar_for_level_expands_include_levels(data_root: Path) -> None:
    pattern = load_grammar_pattern("do", data_root)
    pattern["level"] = "1A"
    save_grammar_pattern("do", pattern, data_root)

    assert {r["id"] for r in grammar_for_level("1A", data_root)} == {"do"}
    assert {r["id"] for r in grammar_for_level("1B", data_root)} == {"do"}

    pattern["level"] = "1B"
    save_grammar_pattern("do", pattern, data_root)
    assert grammar_for_level("1A", data_root) == []
    assert {r["id"] for r in grammar_for_level("1B", data_root)} == {"do"}
