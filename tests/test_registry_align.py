# SPDX-License-Identifier: BSD-3-Clause
"""Registry and verb alignment validators on fixture trees."""

from __future__ import annotations

from pathlib import Path

from soju import db
from soju.align import has_variant, validate_alignment
from soju.registry import validate_registry
from tests.constants import VERB_ID, WORD_ID


def test_validate_registry_ok_on_minimal_fixture(data_root: Path) -> None:
    assert validate_registry(data_root) == []


def test_duplicate_sense_reported(data_root: Path) -> None:
    vocab = db.load_vocabulary(data_root)
    vocab.append(
        {
            "id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
            "hangul": "학교",
            "romanization": "hak-gyo",
            "english": "school",
            "type": "noun",
        }
    )
    db.save_vocabulary(vocab, data_root)
    errors = validate_registry(data_root)
    assert any("Duplicate sense" in e for e in errors)


def test_dangling_ref_reported(data_root: Path) -> None:
    topic = db.load_topic("family", data_root)
    topic["sections"][0]["entries"].append({"ref": "ffffffff-ffff-ffff-ffff-ffffffffffff"})
    db.save_topic("family", topic, data_root)
    errors = validate_registry(data_root)
    assert any("dangling ref" in e for e in errors)


def test_examples_orphan_id(data_root: Path) -> None:
    store = db.load_examples_store(data_root)
    store["ffffffff-ffff-ffff-ffff-ffffffffffff"] = {"default": [{"hangul": "없어요.", "english": "It is gone."}]}
    db.save_examples_store(store, data_root)
    errors = validate_registry(data_root)
    assert any("unknown vocabulary id" in e for e in errors)


def test_validate_alignment_ok(data_root: Path) -> None:
    table = db.load_yaml(db.verb_table_path(data_root))
    verbs = db.vocabulary_by_type("verb", data_root)
    assert validate_alignment(table, verbs, data_root) == []


def test_validate_alignment_missing_form(data_root: Path) -> None:
    forms = db.load_verb_forms_file("present", data_root)
    del forms[VERB_ID]
    db.save_verb_forms_file("present", forms, data_root)
    table = db.load_yaml(db.verb_table_path(data_root))
    verbs = db.vocabulary_by_type("verb", data_root)
    errors = validate_alignment(table, verbs, data_root)
    assert errors
    assert any("missing forms" in e or "missing forms entry" in e for e in errors)


def test_has_variant() -> None:
    assert has_variant({"casual_polite": "가요"}, "casual_polite") is True
    assert has_variant({"casual_polite": "가요"}, "formal_polite") is False
    assert has_variant(None, "casual_polite") is False


def test_word_id_still_referenced(data_root: Path) -> None:
    # Sanity: fixture word remains loadable after other mutations in this module order.
    assert WORD_ID in db.vocabulary_by_id(data_root)
