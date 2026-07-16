# SPDX-License-Identifier: BSD-3-Clause
"""Verb alignment validators on fixture trees."""

from __future__ import annotations

from pathlib import Path

from soju.services.validation.alignment import has_variant, validate_alignment
from tests.constants import VERB_ID
from soju.core.yaml_io import load_yaml
from soju.registry.verbs import load_verb_forms_file, save_verb_forms_file, verb_table_path
from soju.registry.vocabulary import vocabulary_by_type


def test_validate_alignment_ok(data_root: Path) -> None:
    table = load_yaml(verb_table_path(data_root))
    verbs = vocabulary_by_type("verb", data_root)
    assert validate_alignment(table, verbs, data_root) == []


def test_validate_alignment_missing_form(data_root: Path) -> None:
    forms = load_verb_forms_file("present", data_root)
    del forms[VERB_ID]
    save_verb_forms_file("present", forms, data_root)
    table = load_yaml(verb_table_path(data_root))
    verbs = vocabulary_by_type("verb", data_root)
    errors = validate_alignment(table, verbs, data_root)
    assert errors
    assert any("missing forms" in e or "missing forms entry" in e for e in errors)


def test_has_variant() -> None:
    assert has_variant({"casual_polite": "가요"}, "casual_polite") is True
    assert has_variant({"casual_polite": "가요"}, "formal_polite") is False
    assert has_variant(None, "casual_polite") is False
