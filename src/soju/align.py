# SPDX-License-Identifier: BSD-3-Clause
"""Validate verb forms and examples against table layout and vocabulary."""

from __future__ import annotations

import sys

from soju import db


def has_variant(section: dict | None, variant: str) -> bool:
    return isinstance(section, dict) and variant in section


def validate_alignment(table: dict, verbs: list[dict], root=None) -> list[str]:
    errors: list[str] = []
    tense_ids = {section["id"] for section in table.get("sections", [])}
    verbs_by_id = {verb["id"]: verb for verb in verbs}
    examples_store = db.load_examples_store(root)
    forms_by_tense = {tense: db.load_verb_forms_file(tense, root) for tense in tense_ids}

    for tense_id, column in db.iter_verb_columns(table):
        variant = column["variant"]

        if variant == "combined":
            join = column.get("join", [])
            if len(join) < 2:
                errors.append(f"Column '{tense_id}.combined' must list at least two variants in join.")
                continue
            required_variants = join
        else:
            required_variants = [variant]

        forms_file = forms_by_tense.get(tense_id, {})

        for verb in verbs:
            label = verb.get("hangul", verb["id"])
            verb_id = verb["id"]
            forms = forms_file.get(verb_id, {})
            verb_examples = examples_store.get(verb_id, {})
            tense_examples = verb_examples.get(tense_id, {}) if isinstance(verb_examples, dict) and "default" not in verb_examples else {}

            if verb_id not in forms_file:
                errors.append(f"{label}: missing forms entry in {tense_id} file")

            for req in required_variants:
                if not has_variant(forms, req):
                    errors.append(f"{label}: missing forms.{tense_id}.{req}")
                if verb_id in examples_store and isinstance(tense_examples, dict):
                    if tense_examples and not has_variant(tense_examples, req):
                        errors.append(f"{label}: missing examples.{tense_id}.{req}")

    for verb in verbs:
        label = verb.get("hangul", verb["id"])
        verb_id = verb["id"]
        for tense in tense_ids:
            forms_file = forms_by_tense.get(tense, {})
            if verb_id in forms_file:
                for variant in forms_file[verb_id]:
                    if variant not in {
                        col["variant"] for section in table.get("sections", []) if section["id"] == tense for col in section.get("columns", []) if col["variant"] != "combined"
                    }:
                        errors.append(f"{label}: unknown variant '{variant}' under forms.{tense}")

    for tense in tense_ids:
        forms_file = forms_by_tense.get(tense, {})
        for verb_id in forms_file:
            if verb_id not in verbs_by_id:
                errors.append(f"forms/{tense}: unknown verb id {verb_id}")

    return errors


def main() -> int:
    table = db.load_yaml(db.verb_table_path())
    verbs = db.vocabulary_by_type("verb")

    if not isinstance(table, dict):
        print("content/verbs/table.yaml must be a mapping.", file=sys.stderr)
        return 1

    errors = validate_alignment(table, verbs)
    if errors:
        print("Verb data alignment errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("Verb data alignment OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
