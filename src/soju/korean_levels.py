# SPDX-License-Identifier: BSD-3-Clause
"""Korean course level config for AI prompts and vocabulary scoping."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from soju import db

DEFAULT_LEVEL = os.environ.get("SOJU_KOREAN_LEVEL", "1A")
LEVELS_PATH = Path("content") / "levels.yaml"


@dataclass(frozen=True)
class KoreanLevel:
    id: str
    label: str
    description: str
    guidance: str


def _data_root(root: Path | None) -> Path:
    return db.data_root(root)


@lru_cache(maxsize=1)
def _load_levels_raw(root_key: str) -> dict[str, Any]:
    path = Path(root_key) / LEVELS_PATH
    if not path.is_file():
        raise ValueError(f"Missing levels config: {path}")
    data = db.load_yaml(path)
    if not isinstance(data, dict) or "levels" not in data:
        raise ValueError(f"{path} must contain a levels mapping.")
    return data


def load_levels_config(root=None) -> dict[str, Any]:
    return _load_levels_raw(str(_data_root(root)))


def default_level_id(root=None) -> str:
    config = load_levels_config(root)
    default = str(config.get("default", "1A"))
    levels = config.get("levels", {})
    if default not in levels:
        raise ValueError(f"Default level {default!r} is not defined in levels.yaml.")
    return default


def list_level_ids(root=None) -> list[str]:
    config = load_levels_config(root)
    return sorted(config.get("levels", {}))


def resolve_level_id(level_id: str | None, root=None) -> str:
    config = load_levels_config(root)
    levels = config.get("levels", {})
    chosen = (level_id or os.environ.get("SOJU_KOREAN_LEVEL") or config.get("default", "1A")).strip()
    if chosen not in levels:
        known = ", ".join(sorted(levels))
        raise ValueError(f"Unknown Korean level {chosen!r}. Known levels: {known}")
    return chosen


def _expand_level_ids(level_id: str, config: dict[str, Any]) -> list[str]:
    levels = config.get("levels", {})
    if level_id not in levels:
        raise ValueError(f"Unknown Korean level: {level_id}")

    seen: set[str] = set()
    order: list[str] = []

    def visit(level: str) -> None:
        if level in seen:
            return
        seen.add(level)
        entry = levels.get(level, {})
        for parent in entry.get("include_levels", []):
            visit(str(parent))
        order.append(level)

    visit(level_id)
    return order


def get_korean_level(level_id: str | None = None, root=None) -> KoreanLevel:
    config = load_levels_config(root)
    chosen = resolve_level_id(level_id, root)
    entry = config["levels"][chosen]
    return KoreanLevel(
        id=chosen,
        label=str(entry.get("label", chosen)),
        description=str(entry.get("description", "")),
        guidance=str(entry.get("guidance", "")).strip(),
    )


def vocabulary_for_level(level_id: str | None = None, root=None) -> list[dict]:
    config = load_levels_config(root)
    chosen = resolve_level_id(level_id, root)
    included_ids = set(_expand_level_ids(chosen, config))
    fallback = str(config.get("default", "1A"))

    vocabulary = db.load_vocabulary(root)
    filtered: list[dict] = []
    for entry in vocabulary:
        entry_level = str(entry.get("level", fallback))
        if entry_level in included_ids:
            filtered.append(entry)
    return filtered or vocabulary
