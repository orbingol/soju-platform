# SPDX-License-Identifier: BSD-3-Clause
"""Fill verb forms and examples for registry verbs (no CLI)."""

from __future__ import annotations

from soju.languages.plugins import get_language
from soju.registry.examples import load_examples_store, save_examples_store, verb_entry_needs_fill
from soju.registry.verbs import load_verb_forms_file, save_verb_forms_file
from soju.registry.vocabulary import load_vocabulary


def fill_verbs(*, dry_run: bool = False, fill_empty: bool = False, root=None) -> dict[str, int]:
    """Generate verb conjugations and example sentences.

    By default overwrites all verb forms and examples. With ``fill_empty=True``,
    only fills missing forms / missing example cells (leaves existing data).
    """
    lang = get_language()
    vocabulary = load_vocabulary(root)
    verbs = [entry for entry in vocabulary if entry.get("type") == "verb"]
    examples_store = load_examples_store(root)

    present = load_verb_forms_file("present", root)
    past = load_verb_forms_file("past", root)
    future = load_verb_forms_file("future", root)

    filled_forms = 0
    filled_examples = 0
    skipped = 0

    for verb in verbs:
        vid = verb["id"]
        forms = lang.conjugate(verb["hangul"])
        generated_examples = lang.conjugation_examples(verb["hangul"], verb["english"], forms)

        if fill_empty:
            changed = False
            for tense, bucket in (("present", present), ("past", past), ("future", future)):
                existing = bucket.get(vid)
                if not isinstance(existing, dict) or not existing:
                    bucket[vid] = forms[tense]
                    changed = True
            if verb_entry_needs_fill(
                {t: forms[t] for t in ("present", "past", "future")},
                examples_store.get(vid),
            ):
                examples_store[vid] = generated_examples
                filled_examples += 1
                changed = True
            if changed:
                filled_forms += 1
            else:
                skipped += 1
            continue

        present[vid] = forms["present"]
        past[vid] = forms["past"]
        future[vid] = forms["future"]
        examples_store[vid] = generated_examples
        filled_forms += 1
        filled_examples += 1

    if not dry_run:
        save_verb_forms_file("present", present, root)
        save_verb_forms_file("past", past, root)
        save_verb_forms_file("future", future, root)
        save_examples_store(examples_store, root)

    return {
        "verbs": len(verbs),
        "filled_forms": filled_forms,
        "filled_examples": filled_examples,
        "skipped": skipped,
    }
