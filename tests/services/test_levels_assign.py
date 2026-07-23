# SPDX-License-Identifier: BSD-3-Clause
"""Tests for vocabulary level assignment."""

from __future__ import annotations

from pathlib import Path

import pytest

from soju.registry.grammar import load_grammar_pattern, save_grammar_pattern
from soju.registry.vocabulary import load_vocabulary, save_vocabulary
from soju.services.levels_assign import list_unassigned, parse_ids_file, set_levels
from tests.constants import VERB_ID, WORD_ID


def _clear_levels(data_root: Path) -> None:
    vocab = load_vocabulary(data_root)
    for entry in vocab:
        entry.pop("level", None)
    save_vocabulary(vocab, data_root)


def _clear_grammar_levels(data_root: Path) -> None:
    pattern = load_grammar_pattern("do", data_root)
    pattern.pop("level", None)
    save_grammar_pattern("do", pattern, data_root)


def test_list_unassigned_and_type_filter(data_root: Path) -> None:
    _clear_levels(data_root)
    entries = list_unassigned(data_root)
    assert {e["id"] for e in entries} == {WORD_ID, VERB_ID}
    nouns = list_unassigned(data_root, type_id="noun")
    assert [e["id"] for e in nouns] == [WORD_ID]


def test_set_levels_all_unassigned(data_root: Path) -> None:
    _clear_levels(data_root)
    report = set_levels(data_root, level_id="1A", all_unassigned=True)
    assert report.updated == 2
    assert report.dry_run is False
    vocab = load_vocabulary(data_root)
    assert all(e.get("level") == "1A" for e in vocab)
    assert list_unassigned(data_root) == []


def test_set_levels_all_unassigned_dry_run(data_root: Path) -> None:
    _clear_levels(data_root)
    report = set_levels(data_root, level_id="1A", all_unassigned=True, dry_run=True)
    assert report.updated == 2
    assert report.dry_run is True
    assert len(list_unassigned(data_root)) == 2


def test_set_levels_by_ids(data_root: Path) -> None:
    _clear_levels(data_root)
    report = set_levels(data_root, level_id="1B", ids=[WORD_ID])
    assert report.updated == 1
    vocab = {e["id"]: e for e in load_vocabulary(data_root)}
    assert vocab[WORD_ID]["level"] == "1B"
    assert "level" not in vocab[VERB_ID]


def test_set_levels_rejects_mixed_selection(data_root: Path) -> None:
    with pytest.raises(ValueError, match="exactly one selection mode"):
        set_levels(data_root, level_id="1A", all_unassigned=True, ids=[WORD_ID])
    with pytest.raises(ValueError, match="exactly one selection mode"):
        set_levels(data_root, level_id="1A")


def test_set_levels_unknown_id(data_root: Path) -> None:
    with pytest.raises(ValueError, match="Unknown vocabulary id"):
        set_levels(data_root, level_id="1A", ids=["00000000-0000-0000-0000-000000000000"])


def test_set_levels_already_tagged_requires_force(data_root: Path) -> None:
    # Fixture entries are already tagged 1A.
    with pytest.raises(ValueError, match="Already tagged"):
        set_levels(data_root, level_id="1B", ids=[WORD_ID])
    report = set_levels(data_root, level_id="1B", ids=[WORD_ID], force=True)
    assert report.updated == 1
    entry = next(e for e in load_vocabulary(data_root) if e["id"] == WORD_ID)
    assert entry["level"] == "1B"


def test_set_levels_unknown_level(data_root: Path) -> None:
    with pytest.raises(ValueError, match="Unknown language level"):
        set_levels(data_root, level_id="9Z", all_unassigned=True)


def test_parse_ids_file() -> None:
    text = "# comment\n\n" + WORD_ID + "\n  " + VERB_ID + "  \n"
    assert parse_ids_file(text) == [WORD_ID, VERB_ID]


def test_list_unassigned_grammar(data_root: Path) -> None:
    _clear_grammar_levels(data_root)
    rows = list_unassigned(data_root, kind="grammar")
    assert [r["id"] for r in rows] == ["do"]


def test_set_levels_grammar_all_unassigned(data_root: Path) -> None:
    _clear_grammar_levels(data_root)
    report = set_levels(data_root, level_id="1A", kind="grammar", all_unassigned=True)
    assert report.updated == 1
    assert report.kind == "grammar"
    assert load_grammar_pattern("do", data_root)["level"] == "1A"
    assert list_unassigned(data_root, kind="grammar") == []


def test_set_levels_grammar_by_id_requires_force(data_root: Path) -> None:
    # Fixture pattern is already tagged 1A.
    with pytest.raises(ValueError, match="Already tagged"):
        set_levels(data_root, level_id="1B", kind="grammar", ids=["do"])
    report = set_levels(data_root, level_id="1B", kind="grammar", ids=["do"], force=True)
    assert report.updated == 1
    assert load_grammar_pattern("do", data_root)["level"] == "1B"


def test_set_levels_grammar_unknown_id(data_root: Path) -> None:
    with pytest.raises(ValueError, match="Unknown grammar pattern id"):
        set_levels(data_root, level_id="1A", kind="grammar", ids=["missing_pattern"])
