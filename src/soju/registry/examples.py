# SPDX-License-Identifier: BSD-3-Clause
"""Examples store load/save and merge helpers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from soju.core.config import content_root, schema_rel_for
from soju.core.models import EXAMPLE_TENSES, EXAMPLE_VARIANTS
from soju.core.yaml_io import load_yaml, write_examples_yaml_with_schema_comment


def load_examples_store(root: Path | None = None) -> dict:
    """Load the examples store mapping (vocab id → examples)."""
    path = content_root(root) / "registry" / "examples.yaml"
    data = load_yaml(path) if path.exists() else {}
    return data if isinstance(data, dict) else {}


def verb_examples_complete(
    forms: dict[str, dict[str, str]],
    examples: dict[str, Any],
) -> bool:
    """Return True when every non-empty verb form cell has examples."""
    for tense in EXAMPLE_TENSES:
        for variant in EXAMPLE_VARIANTS:
            if forms.get(tense, {}).get(variant) and not examples.get(tense, {}).get(variant):
                return False
    return True


def noun_entry_needs_fill(entry: Any) -> bool:
    """Return True if a noun examples entry is missing a non-empty default list."""
    if not isinstance(entry, dict):
        return True
    default = entry.get("default")
    return not isinstance(default, list) or len(default) == 0


def verb_entry_needs_fill(forms: dict[str, dict[str, str]], entry: Any) -> bool:
    """Return True if a verb examples entry is incomplete for ``forms``."""
    if not isinstance(entry, dict) or "default" in entry:
        return True
    return not verb_examples_complete(forms, entry)


def save_examples_store(data: dict, root: Path | None = None) -> None:
    """Persist the examples store with literal-block YAML formatting."""
    path = content_root(root) / "registry" / "examples.yaml"
    write_examples_yaml_with_schema_comment(
        path,
        schema_rel_for(path, "examples_vocabulary.schema.json", root),
        data,
    )


def merge_default_examples(
    vocab_id: str,
    new_examples: list[dict],
    root: Path | None = None,
    *,
    store: dict | None = None,
    example_key: Callable[[str, str], tuple[str, str]],
) -> int:
    """Append unique default examples for ``vocab_id``; return count merged.

    Args:
        example_key: Caller-supplied ``(hangul, english) -> key`` dedup builder
            (injected by ``services`` so this layer stays plugin-free).
    """
    own_store = store is None
    if own_store:
        store = load_examples_store(root)
    if store is None:
        raise ValueError("examples store is required")
    entry = store.setdefault(vocab_id, {})
    if "default" not in entry or not isinstance(entry["default"], list):
        entry["default"] = []
    existing = entry["default"]
    keys = {example_key(ex["hangul"], ex["english"]) for ex in existing}
    merged = 0
    for ex in new_examples:
        clean = {"hangul": ex["hangul"], "english": ex["english"]}
        key = example_key(clean["hangul"], clean["english"])
        if key in keys:
            continue
        existing.append(clean)
        keys.add(key)
        merged += 1
    if merged and own_store:
        save_examples_store(store, root)
    return merged


def merge_verb_examples(
    vocab_id: str,
    tense: str,
    variant: str,
    new_examples: list[dict],
    root: Path | None = None,
    *,
    store: dict | None = None,
    example_key: Callable[[str, str], tuple[str, str]],
) -> int:
    """Append unique verb examples for a tense/variant cell; return count merged.

    Args:
        example_key: Caller-supplied ``(hangul, english) -> key`` dedup builder
            (injected by ``services`` so this layer stays plugin-free).
    """
    own_store = store is None
    if own_store:
        store = load_examples_store(root)
    if store is None:
        raise ValueError("examples store is required")
    entry = store.setdefault(vocab_id, {})
    tense_map = entry.setdefault(tense, {})
    if not isinstance(tense_map, dict):
        return 0
    variant_list = tense_map.setdefault(variant, [])
    if not isinstance(variant_list, list):
        return 0
    keys = {example_key(ex["hangul"], ex["english"]) for ex in variant_list}
    merged = 0
    for ex in new_examples:
        clean = {"hangul": ex["hangul"], "english": ex["english"]}
        key = example_key(clean["hangul"], clean["english"])
        if key in keys:
            continue
        variant_list.append(clean)
        keys.add(key)
        merged += 1
    if merged and own_store:
        save_examples_store(store, root)
    return merged
