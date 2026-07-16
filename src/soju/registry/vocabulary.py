# SPDX-License-Identifier: BSD-3-Clause
"""Vocabulary registry load/save and indexes."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from soju.core.config import content_root, schema_rel_for
from soju.core.yaml_io import load_yaml, write_yaml_with_schema_comment


def load_vocabulary(root: Path | None = None) -> list[dict]:
    """Load the vocabulary registry list.

    Args:
        root: Optional data-root override.

    Returns:
        List of vocabulary entry mappings.

    Raises:
        ValueError: If the file is not a list.
    """
    path = content_root(root) / "registry" / "vocabulary.yaml"
    data = load_yaml(path) if path.exists() else []
    if data is None:
        return []
    if not isinstance(data, list):
        raise ValueError("content/registry/vocabulary.yaml must be a list.")
    return data


def save_vocabulary(entries: list[dict], root: Path | None = None) -> None:
    """Persist the vocabulary registry list.

    Args:
        entries: Vocabulary entries to write.
        root: Optional data-root override.
    """
    path = content_root(root) / "registry" / "vocabulary.yaml"
    write_yaml_with_schema_comment(
        path,
        schema_rel_for(path, "registry_vocabulary.schema.json", root),
        entries,
    )


def vocabulary_by_id(root: Path | None = None) -> dict[str, dict]:
    """Return vocabulary entries keyed by id."""
    return {entry["id"]: entry for entry in load_vocabulary(root)}


def build_sense_index(
    entries: list[dict],
    *,
    sense_key: Callable[[str, str], tuple[str, str]],
) -> dict[tuple[str, str], dict]:
    """Index entries by sense.

    Args:
        entries: Vocabulary entries.
        sense_key: Caller-supplied ``(hangul, english) -> key`` builder (injected
            by ``services`` so this layer stays plugin-free).

    Returns:
        Mapping of sense key to entry.
    """
    return {sense_key(entry["hangul"], entry["english"]): entry for entry in entries}


def vocabulary_by_sense(
    root: Path | None = None,
    *,
    sense_key: Callable[[str, str], tuple[str, str]],
) -> dict[tuple[str, str], dict]:
    """Return vocabulary entries keyed by sense (see :func:`build_sense_index`)."""
    return build_sense_index(load_vocabulary(root), sense_key=sense_key)


def entries_for_hangul(
    entries: list[dict],
    hangul: str,
    *,
    normalize: Callable[[str], str],
) -> list[dict]:
    """Filter ``entries`` to those whose hangul matches after normalization.

    Args:
        entries: Vocabulary entries.
        hangul: Target term to match.
        normalize: Caller-supplied target-script normalizer (injected).

    Returns:
        Entries whose normalized hangul equals ``normalize(hangul)``.
    """
    key = normalize(hangul)
    return [entry for entry in entries if normalize(entry["hangul"]) == key]


def vocabulary_entries_for_hangul(
    hangul: str,
    root: Path | None = None,
    *,
    normalize: Callable[[str], str],
) -> list[dict]:
    """Load vocabulary and return entries matching ``hangul``."""
    return entries_for_hangul(load_vocabulary(root), hangul, normalize=normalize)


def vocabulary_by_type(type_id: str, root: Path | None = None) -> list[dict]:
    """Return vocabulary entries with the given type id."""
    return [entry for entry in load_vocabulary(root) if entry.get("type") == type_id]
