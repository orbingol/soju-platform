# SPDX-License-Identifier: BSD-3-Clause
"""Promote local topic entries into the vocabulary registry (no CLI)."""

from __future__ import annotations

from soju.base import get_base_language
from soju.registry.examples import load_examples_store, merge_default_examples, save_examples_store
from soju.registry.topics import load_topic, save_topic
from soju.registry.vocabulary import build_sense_index, load_vocabulary, save_vocabulary
from soju.services.keys import example_key, sense_key


def promote_topic(topic_id: str, *, dry_run: bool = False, root=None) -> dict[str, int]:
    topic = load_topic(topic_id, root)
    vocabulary = load_vocabulary(root)
    by_sense = build_sense_index(vocabulary, sense_key=sense_key)
    examples = load_examples_store(root)
    examples_dirty = False
    counts = {"promoted": 0, "skipped": 0}

    for section in topic.get("sections", []):
        updated_entries: list[dict] = []
        for entry in section.get("entries", []):
            if not entry.get("local"):
                updated_entries.append(entry)
                continue

            english = get_base_language().normalize_gloss(entry["english"])
            sense = sense_key(entry["hangul"], english)
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
                    merged = merge_default_examples(entry["id"], entry["examples"], root, store=examples, example_key=example_key)
                    if merged:
                        examples_dirty = True

            updated_entries.append({"ref": entry["id"]})
            counts["promoted"] += 1

        section["entries"] = updated_entries

    if not dry_run:
        save_vocabulary(vocabulary, root)
        save_topic(topic_id, topic, root)
        if examples_dirty:
            save_examples_store(examples, root)

    return counts
