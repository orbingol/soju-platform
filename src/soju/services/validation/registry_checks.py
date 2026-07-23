# SPDX-License-Identifier: BSD-3-Clause
"""Validate vocabulary registry, types, and topic refs (no CLI)."""

from __future__ import annotations

from soju.levels import list_level_ids
from soju.registry.examples import load_examples_store
from soju.registry.grammar import iter_grammar_patterns
from soju.registry.topics import load_topic, load_topics_manifest
from soju.registry.types import load_types
from soju.registry.vocabulary import load_vocabulary, vocabulary_by_id
from soju.services.keys import sense_key


def validate_registry(root=None) -> list[str]:
    """Validate vocabulary registry, types, topic refs, and grammar level tags."""
    errors: list[str] = []
    types = load_types(root)
    type_ids = {entry["id"] for entry in types}
    type_slugs = {entry["slug"] for entry in types}
    known_levels = set(list_level_ids(root))

    vocab_ids: set[str] = set()
    sense_seen: set[tuple[str, str]] = set()

    for entry in load_vocabulary(root):
        vid = entry["id"]
        if vid in vocab_ids:
            errors.append(f"Duplicate vocabulary id: {vid}")
        vocab_ids.add(vid)

        sense = sense_key(entry["hangul"], entry["english"])
        if sense in sense_seen:
            errors.append(f"Duplicate sense: {entry['hangul']} ({entry['english']})")
        sense_seen.add(sense)

        if entry.get("type") not in type_ids:
            errors.append(f"{entry['hangul']}: unknown type '{entry.get('type')}'")

        raw_level = entry.get("level")
        if isinstance(raw_level, str) and raw_level.strip():
            level = raw_level.strip()
            if level not in known_levels:
                errors.append(
                    f"{entry['hangul']} ({vid}): unknown level '{level}' (not in levels.yaml)"
                )

    vocab_by_id = vocabulary_by_id(root)
    manifest = load_topics_manifest(root)

    for topic_id, _meta in manifest.get("topics", {}).items():
        if topic_id in type_slugs:
            errors.append(f"topic id '{topic_id}' collides with type slug")
        topic = load_topic(topic_id, root)
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

    examples_store = load_examples_store(root)
    for vocab_id in examples_store:
        if vocab_id not in vocab_by_id:
            errors.append(f"examples: unknown vocabulary id {vocab_id}")

    errors.extend(validate_grammar_levels(root, known_levels=known_levels))
    return errors


def validate_grammar_levels(root=None, *, known_levels: set[str] | None = None) -> list[str]:
    """Return errors for grammar patterns whose ``level`` is not in ``levels.yaml``."""
    known = known_levels if known_levels is not None else set(list_level_ids(root))
    errors: list[str] = []
    try:
        patterns = iter_grammar_patterns(root)
    except (ValueError, OSError) as exc:
        return [str(exc)]

    for pattern_id, _meta, pattern in patterns:
        raw_level = pattern.get("level")
        if isinstance(raw_level, str) and raw_level.strip():
            level = raw_level.strip()
            if level not in known:
                errors.append(f"grammar pattern {pattern_id}: unknown level '{level}' (not in levels.yaml)")
    return errors
