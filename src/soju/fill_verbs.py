# SPDX-License-Identifier: BSD-3-Clause
"""Fill verb forms and examples for all registry verbs (development utility)."""

from __future__ import annotations

import argparse
import sys

from soju import conjugate, db


def fill_verbs(*, dry_run: bool = False, fill_empty: bool = False, root=None) -> dict[str, int]:
    """Generate verb conjugations and example sentences.

    By default overwrites all verb forms and examples. With ``fill_empty=True``,
    only fills missing forms / missing example cells (leaves existing data).
    """
    vocabulary = db.load_vocabulary(root)
    verbs = [entry for entry in vocabulary if entry.get("type") == "verb"]
    examples_store = db.load_examples_store(root)

    present = db.load_verb_forms_file("present", root)
    past = db.load_verb_forms_file("past", root)
    future = db.load_verb_forms_file("future", root)

    filled_forms = 0
    filled_examples = 0
    skipped = 0

    for verb in verbs:
        vid = verb["id"]
        forms = conjugate.conjugate_verb(verb["hangul"])
        generated_examples = conjugate.examples_for_verb(verb["hangul"], verb["english"], forms)

        if fill_empty:
            changed = False
            for tense, bucket in (("present", present), ("past", past), ("future", future)):
                existing = bucket.get(vid)
                if not isinstance(existing, dict) or not existing:
                    bucket[vid] = forms[tense]
                    changed = True
            if db.verb_entry_needs_fill(
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
        db.save_verb_forms_file("present", present, root)
        db.save_verb_forms_file("past", past, root)
        db.save_verb_forms_file("future", future, root)
        db.save_examples_store(examples_store, root)

    return {
        "verbs": len(verbs),
        "filled_forms": filled_forms,
        "filled_examples": filled_examples,
        "skipped": skipped,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate verb forms and examples for registry verbs.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--fill-empty",
        action="store_true",
        help="Only fill missing forms/examples; leave existing entries unchanged",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when no verbs were updated (useful in automation)",
    )
    args = parser.parse_args(argv)

    try:
        counts = fill_verbs(dry_run=args.dry_run, fill_empty=args.fill_empty)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    mode = "would fill" if args.dry_run else "filled"
    print(
        f"{mode} forms/examples for {counts['filled_forms']}/{counts['verbs']} verbs "
        f"(examples={counts['filled_examples']}, skipped={counts['skipped']})."
    )
    if args.strict and counts["filled_forms"] == 0 and counts["verbs"] > 0:
        print("Error: --strict and nothing was filled.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
