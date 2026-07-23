# SPDX-License-Identifier: BSD-3-Clause
"""``soju levels`` commands for listing and assigning course levels."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from soju.cli._common import flag, make_app
from soju.services.levels_assign import LevelKind, list_unassigned, parse_ids_file, set_levels

app = make_app(help="List and assign vocabulary and grammar course levels.", no_args_is_help=True)

_KIND_HELP = "Target kind: vocabulary (default) or grammar"


def _parse_kind(raw: str) -> LevelKind:
    kind = raw.strip().lower()
    if kind not in {"vocabulary", "grammar"}:
        print("Error: --kind must be 'vocabulary' or 'grammar'.", file=sys.stderr)
        raise typer.Exit(2)
    return kind  # type: ignore[return-value]


@app.command("list-unassigned")
def list_unassigned_cmd(
    format: Annotated[
        str,
        typer.Option("--format", help="Output format: table (default) or ids"),
    ] = "table",
    kind: Annotated[str, typer.Option("--kind", help=_KIND_HELP)] = "vocabulary",
    type_id: Annotated[
        Optional[str],
        typer.Option("--type", help="Filter by vocabulary type id (e.g. noun, verb)"),
    ] = None,
) -> None:
    """List entries with no course level tag."""
    fmt = format.strip().lower()
    if fmt not in {"table", "ids"}:
        print("Error: --format must be 'table' or 'ids'.", file=sys.stderr)
        raise typer.Exit(2)

    parsed_kind = _parse_kind(kind)
    try:
        entries = list_unassigned(kind=parsed_kind, type_id=type_id)
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise typer.Exit(1) from exc

    if fmt == "ids":
        for entry in entries:
            print(entry["id"])
        return

    print(f"{len(entries)} unassigned entr{'y' if len(entries) == 1 else 'ies'}.")
    if parsed_kind == "grammar":
        for entry in entries:
            print(f"{entry['id']}\t{entry.get('form', '')}\t{entry.get('english', '')}")
        return

    for entry in entries:
        print(f"{entry['id']}\t{entry.get('type', '')}\t{entry.get('hangul', '')}\t{entry.get('english', '')}")


@app.command("set")
def set_cmd(
    level: Annotated[str, typer.Option("--level", help="Course level id from levels.yaml")],
    kind: Annotated[str, typer.Option("--kind", help=_KIND_HELP)] = "vocabulary",
    all_unassigned: Annotated[
        bool,
        flag("--all-unassigned", help="Assign every unassigned entry of the chosen kind"),
    ] = False,
    ids: Annotated[
        Optional[list[str]],
        typer.Option("--id", help="Vocabulary UUID or grammar pattern id (repeatable)"),
    ] = None,
    ids_file: Annotated[
        Optional[Path],
        typer.Option("--ids-file", help="File of ids (one per line); use - for stdin"),
    ] = None,
    dry_run: Annotated[bool, flag("--dry-run")] = False,
    force: Annotated[
        bool,
        flag("--force", help="Allow overwriting an existing level tag"),
    ] = False,
) -> None:
    """Assign a course level to selected vocabulary or grammar entries."""
    parsed_kind = _parse_kind(kind)
    selected_ids: list[str] = list(ids or [])
    if ids_file is not None:
        try:
            if str(ids_file) == "-":
                text = sys.stdin.read()
            else:
                text = ids_file.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            raise typer.Exit(1) from exc
        selected_ids.extend(parse_ids_file(text))

    try:
        report = set_levels(
            level_id=level,
            kind=parsed_kind,
            ids=selected_ids or None,
            all_unassigned=all_unassigned,
            dry_run=dry_run,
            force=force,
        )
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise typer.Exit(1) from exc

    mode = "would set" if report.dry_run else "set"
    print(f"{mode} level={report.level_id} on {report.updated} {report.kind} entr{'y' if report.updated == 1 else 'ies'}.")
