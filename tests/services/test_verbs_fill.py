# SPDX-License-Identifier: BSD-3-Clause
"""Verb form fill service."""

from __future__ import annotations

from pathlib import Path

from soju.registry.examples import load_examples_store
from soju.registry.verbs import load_verb_forms_file
from soju.services.verbs_fill import fill_verbs
from tests.constants import VERB_ID


def test_fill_verbs_overwrites_forms_and_examples(data_root: Path) -> None:
    counts = fill_verbs(dry_run=False, fill_empty=False, root=data_root)
    assert counts["verbs"] == 1
    assert counts["filled_forms"] == 1
    assert counts["filled_examples"] == 1
    assert counts["skipped"] == 0
    present = load_verb_forms_file("present", data_root)
    assert present[VERB_ID]["casual_polite"]
    store = load_examples_store(data_root)
    assert "present" in store[VERB_ID]


def test_fill_verbs_fill_empty_skips_complete(data_root: Path) -> None:
    fill_verbs(dry_run=False, fill_empty=False, root=data_root)
    counts = fill_verbs(dry_run=False, fill_empty=True, root=data_root)
    assert counts["skipped"] == 1
    assert counts["filled_forms"] == 0


def test_fill_verbs_dry_run_does_not_write(data_root: Path) -> None:
    before = load_examples_store(data_root)
    counts = fill_verbs(dry_run=True, fill_empty=False, root=data_root)
    assert counts["filled_forms"] == 1
    assert load_examples_store(data_root) == before
