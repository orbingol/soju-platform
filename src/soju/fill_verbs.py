# SPDX-License-Identifier: BSD-3-Clause
"""Fill verb forms and examples for all registry verbs (development utility)."""

from __future__ import annotations

import argparse
import sys

from soju import conjugate, db


def fill_verbs(*, dry_run: bool = False, root=None) -> dict[str, int]:
    vocabulary = db.load_vocabulary(root)
    verbs = [entry for entry in vocabulary if entry.get("type") == "verb"]
    examples_store = db.load_examples_store(root)

    present: dict[str, dict[str, str]] = {}
    past: dict[str, dict[str, str]] = {}
    future: dict[str, dict[str, str]] = {}

    for verb in verbs:
        vid = verb["id"]
        forms = conjugate.conjugate_verb(verb["hangul"])
        present[vid] = forms["present"]
        past[vid] = forms["past"]
        future[vid] = forms["future"]
        examples_store[vid] = conjugate.examples_for_verb(verb["hangul"], verb["english"], forms)

    if not dry_run:
        db.save_verb_forms_file("present", present, root)
        db.save_verb_forms_file("past", past, root)
        db.save_verb_forms_file("future", future, root)
        db.save_examples_store(examples_store, root)

    return {"verbs": len(verbs)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate verb forms and examples for registry verbs.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        counts = fill_verbs(dry_run=args.dry_run)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    mode = "would fill" if args.dry_run else "filled"
    print(f"{mode} forms and examples for {counts['verbs']} verbs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
