# SPDX-License-Identifier: BSD-3-Clause
"""Deterministic (non-LLM) example fill via the language plugin."""

from __future__ import annotations

from typing import Any

from soju.core.models import EXAMPLE_TENSES as TENSES
from soju.core.models import EXAMPLE_VARIANTS as VARIANTS
from soju.languages.plugins import get_language
from soju.levels import vocabulary_for_level
from soju.registry.examples import load_examples_store, noun_entry_needs_fill, verb_entry_needs_fill
from soju.registry.verbs import load_verb_forms, load_verb_forms_cache


def fill_examples_local(
    *,
    level_id: str,
    verbs: bool,
    nouns: bool,
    examples_per: int,
    fill_mode: str,
    root=None,
) -> tuple[dict[str, Any], int]:
    """Fill examples using the active language plugin's deterministic generators.

    Targets the course band for ``level_id`` **plus** unassigned vocabulary so newly
    imported/promoted rows (omit ``level``) still receive examples. Higher-level
    tagged entries remain excluded.
    """
    lang = get_language()
    examples_store = load_examples_store(root)
    updated = 0
    band = vocabulary_for_level(level_id, root, include_unassigned=True)

    if verbs:
        verb_entries = [e for e in band if e.get("type") == "verb"]
        forms_cache = load_verb_forms_cache(root)
        for verb in verb_entries:
            forms = load_verb_forms(verb["id"], root, cache=forms_cache)
            if not all(forms.get(t, {}).get(v) for t in TENSES for v in VARIANTS):
                continue
            if fill_mode == "fill-empty" and not verb_entry_needs_fill(forms, examples_store.get(verb["id"])):
                continue
            examples_store[verb["id"]] = lang.examples_for_verb(
                verb["hangul"],
                verb["english"],
                forms,
                level_id=level_id,
            )
            updated += 1

    if nouns:
        noun_entries = [e for e in band if e.get("type") == "noun"]
        for noun in noun_entries:
            if fill_mode == "fill-empty" and not noun_entry_needs_fill(examples_store.get(noun["id"])):
                continue
            examples_store[noun["id"]] = {
                "default": lang.examples_for_noun(
                    noun["hangul"],
                    noun["english"],
                    level_id=level_id,
                    examples_per=examples_per,
                )
            }
            updated += 1

    return examples_store, updated
