# SPDX-License-Identifier: BSD-3-Clause
"""Topic manifest and topic file load/save helpers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from soju.core.config import content_root, schema_rel_for
from soju.core.yaml_io import load_yaml, write_yaml_with_schema_comment


def load_topics_manifest(root: Path | None = None) -> dict:
    """Load ``content/topics/manifest.yaml``.

    Raises:
        ValueError: If the manifest is not a mapping.
    """
    manifest = load_yaml(content_root(root) / "topics" / "manifest.yaml")
    if not isinstance(manifest, dict):
        raise ValueError("content/topics/manifest.yaml must be a mapping.")
    return manifest


def topic_path(topic_id: str, root: Path | None = None) -> Path:
    """Return the path to a topic YAML file.

    Raises:
        KeyError: If ``topic_id`` is not in the manifest.
    """
    manifest = load_topics_manifest(root)
    topics = manifest.get("topics", {})
    if topic_id not in topics:
        raise KeyError(f"Unknown topic: {topic_id}")
    return content_root(root) / "topics" / topic_id / "topic.yaml"


def load_topic(topic_id: str, root: Path | None = None) -> dict:
    """Load a topic document, defaulting to an empty sections list."""
    path = topic_path(topic_id, root)
    data = load_yaml(path) if path.exists() else {"sections": []}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a mapping with sections.")
    data.setdefault("sections", [])
    return data


def save_topic(topic_id: str, data: dict, root: Path | None = None) -> None:
    """Persist a topic document with a schema comment."""
    path = topic_path(topic_id, root)
    write_yaml_with_schema_comment(
        path,
        schema_rel_for(path, "topics_topic.schema.json", root),
        data,
    )


def iter_topic_entries(topic: dict) -> list[dict]:
    """Flatten all section entries from a topic document."""
    entries: list[dict] = []
    for section in topic.get("sections", []):
        entries.extend(section.get("entries", []))
    return entries


def topic_has_ref(topic: dict, vocab_id: str) -> bool:
    """Return True if ``vocab_id`` appears as a ref or local id in the topic."""
    for entry in iter_topic_entries(topic):
        if entry.get("ref") == vocab_id:
            return True
        if entry.get("id") == vocab_id:
            return True
    return False


def find_local_entry(
    topic: dict,
    hangul: str,
    english: str | None = None,
    *,
    normalize: Callable[[str], str],
    match_gloss: Callable[[str], str],
) -> dict | None:
    """Find a local topic entry by hangul (and optional english identity).

    Args:
        topic: Topic document.
        hangul: Target term to match.
        english: Optional base gloss to disambiguate senses.
        normalize: Caller-supplied target-script normalizer (injected).
        match_gloss: Caller-supplied base-gloss identity builder (injected).

    Returns:
        The matching local entry, or ``None``.
    """
    key = normalize(hangul)
    english_key = match_gloss(english) if english is not None else None
    for entry in iter_topic_entries(topic):
        if not entry.get("local"):
            continue
        if normalize(entry.get("hangul", "")) != key:
            continue
        if english_key is not None and match_gloss(entry.get("english", "")) != english_key:
            continue
        return entry
    return None


def find_section(topic: dict, section_id: str) -> dict | None:
    """Return the section mapping with ``section_id``, if any."""
    for section in topic.get("sections", []):
        if section.get("id") == section_id:
            return section
    return None
