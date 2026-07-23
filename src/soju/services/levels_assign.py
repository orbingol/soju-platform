# SPDX-License-Identifier: BSD-3-Clause
"""List and assign course levels on vocabulary and grammar entries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from soju.levels import resolve_level_id
from soju.registry.grammar import iter_grammar_patterns, load_grammar_pattern, save_grammar_pattern
from soju.registry.vocabulary import load_vocabulary, save_vocabulary

LevelKind = Literal["vocabulary", "grammar"]


def is_unassigned(entry: dict[str, Any]) -> bool:
    """Return True when the entry has no course ``level`` tag."""
    raw = entry.get("level")
    return raw is None or (isinstance(raw, str) and not str(raw).strip())


def list_unassigned(
    root: Path | None = None,
    *,
    kind: LevelKind = "vocabulary",
    type_id: str | None = None,
) -> list[dict[str, Any]]:
    """Return unassigned vocabulary rows or grammar pattern summaries."""
    if kind == "vocabulary":
        entries = [e for e in load_vocabulary(root) if is_unassigned(e)]
        if type_id:
            entries = [e for e in entries if e.get("type") == type_id]
        return entries

    if type_id:
        raise ValueError("--type applies only to --kind vocabulary.")

    rows: list[dict[str, Any]] = []
    for pattern_id, _meta, pattern in iter_grammar_patterns(root):
        if is_unassigned(pattern):
            rows.append(
                {
                    "id": pattern_id,
                    "form": pattern.get("form", ""),
                    "english": pattern.get("english", ""),
                    "category": pattern.get("category", ""),
                }
            )
    return rows


@dataclass(frozen=True)
class SetLevelsReport:
    """Result of a :func:`set_levels` call."""

    updated: int
    level_id: str
    dry_run: bool
    kind: LevelKind


def set_levels(
    root: Path | None = None,
    *,
    level_id: str,
    kind: LevelKind = "vocabulary",
    ids: list[str] | None = None,
    all_unassigned: bool = False,
    dry_run: bool = False,
    force: bool = False,
) -> SetLevelsReport:
    """Set ``level`` on selected vocabulary or grammar entries.

    Exactly one selection mode is required: ``all_unassigned=True`` **or** a non-empty
    ``ids`` list (from ``--id`` / ``--ids-file``).

    Raises:
        ValueError: On invalid selection, unknown level/id, or tagged entry without ``force``.
    """
    if kind not in {"vocabulary", "grammar"}:
        raise ValueError("--kind must be 'vocabulary' or 'grammar'.")

    resolved = resolve_level_id(level_id, root)
    id_list = [i.strip() for i in (ids or []) if i and str(i).strip()]
    has_ids = bool(id_list)

    if all_unassigned == has_ids:
        raise ValueError("Choose exactly one selection mode: --all-unassigned, or --id / --ids-file.")

    if kind == "vocabulary":
        return _set_vocabulary_levels(
            root,
            resolved=resolved,
            id_list=id_list,
            all_unassigned=all_unassigned,
            dry_run=dry_run,
            force=force,
        )
    return _set_grammar_levels(
        root,
        resolved=resolved,
        id_list=id_list,
        all_unassigned=all_unassigned,
        dry_run=dry_run,
        force=force,
    )


def _set_vocabulary_levels(
    root: Path | None,
    *,
    resolved: str,
    id_list: list[str],
    all_unassigned: bool,
    dry_run: bool,
    force: bool,
) -> SetLevelsReport:
    vocabulary = load_vocabulary(root)
    by_id = {str(entry["id"]): entry for entry in vocabulary}

    if all_unassigned:
        targets = [entry for entry in vocabulary if is_unassigned(entry)]
    else:
        missing = [vid for vid in id_list if vid not in by_id]
        if missing:
            raise ValueError(f"Unknown vocabulary id(s): {', '.join(missing)}")
        already = [vid for vid in id_list if not is_unassigned(by_id[vid]) and not force]
        if already:
            raise ValueError("Already tagged (pass --force to overwrite): " + ", ".join(already))
        targets = [by_id[vid] for vid in id_list]

    for entry in targets:
        entry["level"] = resolved

    if not dry_run and targets:
        save_vocabulary(vocabulary, root)

    return SetLevelsReport(updated=len(targets), level_id=resolved, dry_run=dry_run, kind="vocabulary")


def _set_grammar_levels(
    root: Path | None,
    *,
    resolved: str,
    id_list: list[str],
    all_unassigned: bool,
    dry_run: bool,
    force: bool,
) -> SetLevelsReport:
    patterns = {pattern_id: pattern for pattern_id, _meta, pattern in iter_grammar_patterns(root)}

    if all_unassigned:
        target_ids = [pid for pid, pattern in patterns.items() if is_unassigned(pattern)]
    else:
        missing = [pid for pid in id_list if pid not in patterns]
        if missing:
            raise ValueError(f"Unknown grammar pattern id(s): {', '.join(missing)}")
        already = [pid for pid in id_list if not is_unassigned(patterns[pid]) and not force]
        if already:
            raise ValueError("Already tagged (pass --force to overwrite): " + ", ".join(already))
        target_ids = list(id_list)

    if not dry_run:
        for pattern_id in target_ids:
            pattern = load_grammar_pattern(pattern_id, root)
            pattern["level"] = resolved
            save_grammar_pattern(pattern_id, pattern, root)

    return SetLevelsReport(updated=len(target_ids), level_id=resolved, dry_run=dry_run, kind="grammar")


def parse_ids_file(text: str) -> list[str]:
    """Parse id lines from a file (blank lines and ``#`` comments ignored)."""
    ids: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        ids.append(stripped)
    return ids
