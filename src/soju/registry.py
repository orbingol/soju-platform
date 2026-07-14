# SPDX-License-Identifier: BSD-3-Clause
"""Validate vocabulary registry, types, and topic refs."""

from __future__ import annotations

import sys

from soju import db


def validate_registry(root=None) -> list[str]:
    errors: list[str] = []
    type_ids = {entry["id"] for entry in db.load_types(root)}
    type_slugs = {entry["slug"] for entry in db.load_types(root)}

    vocab_ids: set[str] = set()
    sense_seen: set[tuple[str, str]] = set()

    for entry in db.load_vocabulary(root):
        vid = entry["id"]
        if vid in vocab_ids:
            errors.append(f"Duplicate vocabulary id: {vid}")
        vocab_ids.add(vid)

        sense = db.sense_key(entry["hangul"], entry["english"])
        if sense in sense_seen:
            errors.append(f"Duplicate sense: {entry['hangul']} ({entry['english']})")
        sense_seen.add(sense)

        if entry.get("type") not in type_ids:
            errors.append(f"{entry['hangul']}: unknown type '{entry.get('type')}'")

    vocab_by_id = db.vocabulary_by_id(root)
    manifest = db.load_topics_manifest(root)

    for topic_id, _meta in manifest.get("topics", {}).items():
        if topic_id in type_slugs:
            errors.append(f"topic id '{topic_id}' collides with type slug")
        topic = db.load_topic(topic_id, root)
        seen_refs: set[str] = set()
        for section in topic.get("sections", []):
            for entry in section.get("entries", []):
                if "ref" in entry:
                    ref = entry["ref"]
                    if ref in seen_refs:
                        errors.append(f"topic {topic_id}: duplicate ref {ref}")
                    seen_refs.add(ref)
                    if ref not in vocab_by_id:
                        errors.append(f"topic {topic_id}: dangling ref {ref}")
                elif entry.get("local"):
                    required = {"id", "local", "hangul", "romanization", "english"}
                    missing = required - set(entry)
                    if missing:
                        errors.append(f"topic {topic_id}: local entry missing fields {sorted(missing)}")
                    if entry.get("id") in vocab_ids:
                        errors.append(f"topic {topic_id}: local id collides with registry id {entry['id']}")
                else:
                    errors.append(f"topic {topic_id}: entry must have ref or local: true")

    examples_store = db.load_examples_store(root)
    for vocab_id in examples_store:
        if vocab_id not in vocab_by_id:
            errors.append(f"examples: unknown vocabulary id {vocab_id}")

    return errors


def main() -> int:
    errors = validate_registry()
    if errors:
        print("Registry validation errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("Registry validation OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
