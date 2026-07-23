# SPDX-License-Identifier: BSD-3-Clause
"""Registry validators on fixture trees."""

from __future__ import annotations

from pathlib import Path

from soju.services.validation.registry_checks import validate_registry
from tests.constants import WORD_ID
from soju.registry.examples import load_examples_store, save_examples_store
from soju.registry.topics import load_topic, save_topic
from soju.registry.vocabulary import load_vocabulary, save_vocabulary, vocabulary_by_id


def test_validate_registry_ok_on_minimal_fixture(data_root: Path) -> None:
    assert validate_registry(data_root) == []


def test_duplicate_sense_reported(data_root: Path) -> None:
    vocab = load_vocabulary(data_root)
    vocab.append(
        {
            "id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
            "hangul": "학교",
            "romanization": "hak-gyo",
            "english": "school",
            "type": "noun",
        }
    )
    save_vocabulary(vocab, data_root)
    errors = validate_registry(data_root)
    assert any("Duplicate sense" in e for e in errors)


def test_dangling_ref_reported(data_root: Path) -> None:
    topic = load_topic("family", data_root)
    topic["sections"][0]["entries"].append({"ref": "ffffffff-ffff-ffff-ffff-ffffffffffff"})
    save_topic("family", topic, data_root)
    errors = validate_registry(data_root)
    assert any("dangling ref" in e for e in errors)


def test_examples_orphan_id(data_root: Path) -> None:
    store = load_examples_store(data_root)
    store["ffffffff-ffff-ffff-ffff-ffffffffffff"] = {"default": [{"hangul": "없어요.", "english": "It is gone."}]}
    save_examples_store(store, data_root)
    errors = validate_registry(data_root)
    assert any("unknown vocabulary id" in e for e in errors)


def test_word_id_still_referenced(data_root: Path) -> None:
    # Sanity: fixture word remains loadable after other mutations in this module order.
    assert WORD_ID in vocabulary_by_id(data_root)


def test_unknown_level_reported(data_root: Path) -> None:
    vocab = load_vocabulary(data_root)
    for entry in vocab:
        if entry["id"] == WORD_ID:
            entry["level"] = "9Z"
            break
    save_vocabulary(vocab, data_root)
    errors = validate_registry(data_root)
    assert any("unknown level '9Z'" in e and WORD_ID in e for e in errors)


def test_omitted_level_ok(data_root: Path) -> None:
    vocab = load_vocabulary(data_root)
    for entry in vocab:
        entry.pop("level", None)
    save_vocabulary(vocab, data_root)
    assert validate_registry(data_root) == []


def test_valid_level_ok(data_root: Path) -> None:
    vocab = load_vocabulary(data_root)
    for entry in vocab:
        entry["level"] = "1A"
    save_vocabulary(vocab, data_root)
    assert validate_registry(data_root) == []
