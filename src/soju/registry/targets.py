# SPDX-License-Identifier: BSD-3-Clause
"""Manifest-driven paths for JSON Schema validation."""

from __future__ import annotations

from pathlib import Path

from soju.core.config import content_root, data_root
from soju.core.yaml_io import load_yaml
from soju.registry.topics import load_topics_manifest, topic_path
from soju.registry.verbs import load_verb_manifest


def glob_validate_targets(root: Path | None = None) -> dict[str, list[str]]:
    """Return schema-name → data-file paths for ``soju validate-schemas``.

    Args:
        root: Optional data-root override.

    Returns:
        Mapping of logical target names to absolute/relative file path strings.
    """
    base = content_root(root)
    data = data_root(root)
    verb_manifest = load_verb_manifest(root)
    topics_manifest = load_topics_manifest(root)

    topic_files = [topic_path(topic_id, root).as_posix() for topic_id in sorted(topics_manifest.get("topics", {}))]

    topic_table_files = [(base / "topics" / "table.yaml").as_posix()]
    for topic_id in sorted(topics_manifest.get("topics", {})):
        override = base / "topics" / topic_id / "table.yaml"
        if override.is_file():
            topic_table_files.append(override.as_posix())

    form_files = [(base / "verbs" / rel).as_posix() for rel in sorted(verb_manifest.get("forms", {}).values())]
    construction_files = [(base / "verbs" / rel).as_posix() for rel in sorted(verb_manifest.get("constructions", {}).values())]

    staging_exercises = sorted(p.as_posix() for p in (data / "staging" / "exercises").glob("*.yaml"))
    staging_stories = sorted(p.as_posix() for p in (data / "staging" / "stories").glob("*.yaml"))

    grammar_manifest_path = base / "grammar" / "manifest.yaml"
    grammar_pattern_files: list[str] = []
    if grammar_manifest_path.exists():
        grammar_manifest = load_yaml(grammar_manifest_path)
        if isinstance(grammar_manifest, dict):
            for meta in grammar_manifest.get("patterns", {}).values():
                if isinstance(meta, dict) and meta.get("path"):
                    grammar_pattern_files.append((base / "grammar" / meta["path"]).as_posix())

    return {
        "registry-types": [(base / "registry" / "types.yaml").as_posix()],
        "registry-vocabulary": [(base / "registry" / "vocabulary.yaml").as_posix()],
        "examples-vocabulary": [(base / "registry" / "examples.yaml").as_posix()],
        "words-table": [(base / "words" / "table.yaml").as_posix()],
        "topics-manifest": [(base / "topics" / "manifest.yaml").as_posix()],
        "topics-table": topic_table_files,
        "topics-topics": topic_files,
        "verb-manifest": [(base / "verbs" / "manifest.yaml").as_posix()],
        "verb-table": [(base / "verbs" / "table.yaml").as_posix()],
        "verb-forms": form_files,
        "verb-constructions": construction_files,
        "grammar-manifest": [grammar_manifest_path.as_posix()],
        "grammar-patterns": grammar_pattern_files,
        "staging-vocabulary": [(data / "staging" / "vocabulary-candidates.yaml").as_posix()],
        "staging-exercises": staging_exercises,
        "staging-stories": staging_stories,
        "practice-themes": [(base / "practice" / "themes.yaml").as_posix()],
    }
