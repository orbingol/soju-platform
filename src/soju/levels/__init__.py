# SPDX-License-Identifier: BSD-3-Clause
"""Course language-level configuration and vocabulary/grammar filtering."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from soju.core.config import data_root as _resolve_data_root
from soju.core.yaml_io import load_yaml
from soju.registry.grammar import iter_grammar_patterns
from soju.registry.vocabulary import load_vocabulary

ENV_LANGUAGE_LEVEL = "SOJU_LANGUAGE_LEVEL"

LEVELS_PATH = Path("content") / "levels.yaml"


def _env_level() -> str | None:
    """Return ``SOJU_LANGUAGE_LEVEL`` when set."""
    return os.environ.get(ENV_LANGUAGE_LEVEL)


DEFAULT_LEVEL = _env_level() or "1A"


@dataclass(frozen=True)
class LanguageLevel:
    """A course level used for prompts and vocabulary scoping."""

    id: str
    label: str
    description: str
    guidance: str


def _data_root(root: Path | None) -> Path:
    """Resolve the data root for levels config."""
    return _resolve_data_root(root)


@lru_cache(maxsize=1)
def _load_levels_raw(root_key: str) -> dict[str, Any]:
    """Load and cache ``content/levels.yaml`` for a data-root path string."""
    path = Path(root_key) / LEVELS_PATH
    if not path.is_file():
        raise ValueError(f"Missing levels config: {path}")
    data = load_yaml(path)
    if not isinstance(data, dict) or "levels" not in data:
        raise ValueError(f"{path} must contain a levels mapping.")
    return data


def load_levels_config(root=None) -> dict[str, Any]:
    """Load the levels configuration mapping from ``content/levels.yaml``."""
    return _load_levels_raw(_data_root(root).as_posix())


def default_level_id(root=None) -> str:
    """Return the configured default level id."""
    config = load_levels_config(root)
    default = str(config.get("default", "1A"))
    levels = config.get("levels", {})
    if default not in levels:
        raise ValueError(f"Default level {default!r} is not defined in levels.yaml.")
    return default


def list_level_ids(root=None) -> list[str]:
    """Return sorted level ids defined in the config."""
    config = load_levels_config(root)
    return sorted(config.get("levels", {}))


def resolve_level_id(level_id: str | None, root=None) -> str:
    """Resolve a level id from an argument, env, or config default.

    Raises:
        ValueError: If the chosen id is not defined.
    """
    config = load_levels_config(root)
    levels = config.get("levels", {})
    chosen = (level_id or _env_level() or config.get("default", "1A")).strip()
    if chosen not in levels:
        known = ", ".join(sorted(levels))
        raise ValueError(f"Unknown language level {chosen!r}. Known levels: {known}")
    return chosen


def _expand_level_ids(level_id: str, config: dict[str, Any]) -> list[str]:
    """Return ``level_id`` plus parents from ``include_levels``, parents first."""
    levels = config.get("levels", {})
    if level_id not in levels:
        raise ValueError(f"Unknown language level: {level_id}")

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


def _included_level_ids(level_id: str | None, root) -> set[str]:
    """Resolve ``level_id`` and return the expanded course-band id set."""
    config = load_levels_config(root)
    chosen = resolve_level_id(level_id, root)
    return set(_expand_level_ids(chosen, config))


def _is_unassigned_level(raw: Any) -> bool:
    """Return True when ``raw`` is missing or blank (unassigned)."""
    return raw is None or (isinstance(raw, str) and not str(raw).strip())


def _matches_course_band(raw_level: Any, included_ids: set[str], include_unassigned: bool) -> bool:
    """Return True when a vocab/grammar ``level`` belongs in the course band."""
    if _is_unassigned_level(raw_level):
        return include_unassigned
    return str(raw_level).strip() in included_ids


def get_language_level(level_id: str | None = None, root=None) -> LanguageLevel:
    """Return a :class:`LanguageLevel` for the resolved level id."""
    config = load_levels_config(root)
    chosen = resolve_level_id(level_id, root)
    entry = config["levels"][chosen]
    return LanguageLevel(
        id=chosen,
        label=str(entry.get("label", chosen)),
        description=str(entry.get("description", "")),
        guidance=str(entry.get("guidance", "")).strip(),
    )


def vocabulary_for_level(
    level_id: str | None = None,
    root=None,
    *,
    include_unassigned: bool = False,
) -> list[dict]:
    """Return vocabulary entries for ``level_id`` (and ``include_levels`` parents).

    Entries with a ``level`` field are included when that id is in the expanded
    course set. Entries with no ``level`` are **unassigned**: excluded by default,
    included when ``include_unassigned`` is true.
    """
    included_ids = _included_level_ids(level_id, root)
    return [entry for entry in load_vocabulary(root) if _matches_course_band(entry.get("level"), included_ids, include_unassigned)]


def grammar_for_level(
    level_id: str | None = None,
    root=None,
    *,
    include_unassigned: bool = False,
) -> list[dict]:
    """Return grammar pattern dicts for ``level_id`` (and ``include_levels`` parents).

    Same membership rules as :func:`vocabulary_for_level`. Each row is the pattern
    YAML mapping with ``id`` set from the manifest key when missing.
    """
    included_ids = _included_level_ids(level_id, root)
    rows: list[dict] = []
    for pattern_id, _meta, pattern in iter_grammar_patterns(root):
        if not _matches_course_band(pattern.get("level"), included_ids, include_unassigned):
            continue
        row = dict(pattern)
        row.setdefault("id", pattern_id)
        rows.append(row)
    return rows
