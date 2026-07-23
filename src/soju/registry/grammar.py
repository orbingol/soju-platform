# SPDX-License-Identifier: BSD-3-Clause
"""Grammar manifest and pattern file load/save."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from soju.core.config import content_root, schema_rel_for
from soju.core.yaml_io import load_yaml, write_yaml_with_schema_comment

GRAMMAR_DIR = Path("grammar")
MANIFEST_NAME = "manifest.yaml"


def grammar_root(root: Path | None = None) -> Path:
    """Return ``content/grammar`` under the data root."""
    return content_root(root) / GRAMMAR_DIR


def load_grammar_manifest(root: Path | None = None) -> dict[str, Any]:
    """Load ``grammar/manifest.yaml`` (empty patterns when missing)."""
    path = grammar_root(root) / MANIFEST_NAME
    if not path.is_file():
        return {"patterns": {}}
    data = load_yaml(path)
    if not isinstance(data, dict):
        raise ValueError("content/grammar/manifest.yaml must be a mapping.")
    patterns = data.get("patterns", {})
    if patterns is None:
        patterns = {}
    if not isinstance(patterns, dict):
        raise ValueError("content/grammar/manifest.yaml patterns must be a mapping.")
    return {"patterns": patterns}


def pattern_path(pattern_id: str, root: Path | None = None) -> Path:
    """Resolve the on-disk path for a grammar pattern id via the manifest."""
    patterns = load_grammar_manifest(root)["patterns"]
    meta = patterns.get(pattern_id)
    if not isinstance(meta, dict):
        raise ValueError(f"Unknown grammar pattern id: {pattern_id}")
    rel = meta.get("path")
    if not isinstance(rel, str) or not rel.strip():
        raise ValueError(f"Grammar pattern {pattern_id!r} is missing a path in the manifest.")
    return grammar_root(root) / rel


def load_grammar_pattern(pattern_id: str, root: Path | None = None) -> dict[str, Any]:
    """Load one grammar pattern YAML file."""
    path = pattern_path(pattern_id, root)
    data = load_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(f"Grammar pattern file must be a mapping: {path}")
    return data


def save_grammar_pattern(pattern_id: str, data: dict[str, Any], root: Path | None = None) -> None:
    """Persist one grammar pattern YAML file with its schema comment."""
    path = pattern_path(pattern_id, root)
    write_yaml_with_schema_comment(
        path,
        schema_rel_for(path, "grammar_pattern.schema.json", root),
        data,
    )


def iter_grammar_patterns(root: Path | None = None) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    """Return ``(pattern_id, manifest_meta, pattern_data)`` for every manifest entry."""
    rows: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for pattern_id, meta in sorted(load_grammar_manifest(root)["patterns"].items()):
        if not isinstance(meta, dict):
            continue
        rows.append((str(pattern_id), meta, load_grammar_pattern(str(pattern_id), root)))
    return rows
