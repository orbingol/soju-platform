# SPDX-License-Identifier: BSD-3-Clause
"""Promote local topic entries into the vocabulary registry."""

from __future__ import annotations

import argparse
import sys

from soju import db


def promote_topic(topic_id: str, *, dry_run: bool = False, root=None) -> dict[str, int]:
    topic = db.load_topic(topic_id, root)
    vocabulary = db.load_vocabulary(root)
    by_sense = db.build_sense_index(vocabulary)
    examples = db.load_examples_store(root)
    examples_dirty = False
    counts = {"promoted": 0, "skipped": 0}

    for section in topic.get("sections", []):
        updated_entries: list[dict] = []
        for entry in section.get("entries", []):
            if not entry.get("local"):
                updated_entries.append(entry)
                continue

            english = db.normalize_english_gloss(entry["english"])
            sense = db.sense_key(entry["hangul"], english)
            if sense in by_sense:
                counts["skipped"] += 1
                updated_entries.append({"ref": by_sense[sense]["id"]})
                continue

            registry_entry = {
                "id": entry["id"],
                "hangul": entry["hangul"],
                "romanization": entry["romanization"],
                "english": english,
                "type": entry.get("type", "noun"),
            }

            if not dry_run:
                vocabulary.append(registry_entry)
                by_sense[sense] = registry_entry
                if entry.get("examples"):
                    merged = db.merge_default_examples(entry["id"], entry["examples"], root, store=examples)
                    if merged:
                        examples_dirty = True

            updated_entries.append({"ref": entry["id"]})
            counts["promoted"] += 1

        section["entries"] = updated_entries

    if not dry_run:
        db.save_vocabulary(vocabulary, root)
        db.save_topic(topic_id, topic, root)
        if examples_dirty:
            db.save_examples_store(examples, root)

    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Promote local topic entries to registry.")
    parser.add_argument("--topic", required=True, help="Topic id (e.g. family)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        counts = promote_topic(args.topic, dry_run=args.dry_run)
    except (KeyError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    mode = "would promote" if args.dry_run else "promoted"
    print(f"{mode} {counts['promoted']} entries; skipped {counts['skipped']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
