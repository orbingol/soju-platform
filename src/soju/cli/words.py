# SPDX-License-Identifier: BSD-3-Clause
"""``soju-import`` words / verbs subcommands."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from soju.cli._common import flag, make_app
from soju.services.intake import (
    ImportReport,
    ImportSession,
    import_verb_record,
    import_word_record,
    import_words_from_lines,
    import_words_from_staging,
    load_records_json,
)

app = make_app(
    help="Import vocabulary into Soju data files.",
    no_args_is_help=True,
)


@app.command("words")
def words(
    topic: Annotated[str, typer.Option("--topic", help="Topic id from topics manifest")],
    dry_run: Annotated[bool, flag("--dry-run")] = False,
    section: Annotated[Optional[str], typer.Option("--section", help="Section id within the topic (required if multiple)")] = None,
    file: Annotated[Optional[Path], typer.Option("--file", help="Plain-text word list file")] = None,
    stdin_json: Annotated[bool, flag("--stdin-json", help="Read JSON records from stdin")] = False,
    from_staging: Annotated[
        Optional[Path],
        typer.Option("--from-staging", help="Staging YAML file path"),
    ] = None,
) -> None:
    """Import words into a topic."""
    report = ImportReport()
    try:
        session = ImportSession.open_words(topic)
        if from_staging is not None:
            import_words_from_staging(
                from_staging,
                session,
                report,
                section_id=section,
                dry_run=dry_run,
            )
        elif stdin_json:
            for record in load_records_json(True, None):
                import_word_record(
                    record,
                    session,
                    report,
                    section_id=section,
                    dry_run=dry_run,
                )
        elif file is not None:
            lines = file.read_text(encoding="utf-8").splitlines()
            import_words_from_lines(
                lines,
                session,
                report,
                section_id=section,
                dry_run=dry_run,
            )
        else:
            print("Provide --file, --stdin-json, or --from-staging.", file=sys.stderr)
            raise typer.Exit(2)
        session.commit(dry_run=dry_run)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise typer.Exit(1) from exc

    prefix = "[dry-run] " if dry_run else ""
    print(f"{prefix}{report.summary()}")
    for note in report.notes:
        print(f"  note: {note}", file=sys.stderr)
    for error in report.errors:
        print(f"  error: {error}", file=sys.stderr)
    if report.errors and report.added == 0 and report.merged_examples == 0:
        raise typer.Exit(1)


@app.command("verbs")
def verbs(
    dry_run: Annotated[bool, flag("--dry-run")] = False,
    file: Annotated[Optional[Path], typer.Option("--file", help="Not supported without --stdin-json")] = None,
    stdin_json: Annotated[bool, flag("--stdin-json", help="Read JSON records from stdin")] = False,
) -> None:
    """Import verbs."""
    report = ImportReport()
    try:
        session = ImportSession.open_verbs()
        if stdin_json:
            for record in load_records_json(True, None):
                import_verb_record(record, session, report, dry_run=dry_run)
        elif file is not None:
            print(
                "Verb file import requires --stdin-json with full conjugations.",
                file=sys.stderr,
            )
            raise typer.Exit(2)
        else:
            print("Provide --stdin-json for verbs.", file=sys.stderr)
            raise typer.Exit(2)
        session.commit(dry_run=dry_run)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise typer.Exit(1) from exc

    prefix = "[dry-run] " if dry_run else ""
    print(f"{prefix}{report.summary()}")
    for note in report.notes:
        print(f"  note: {note}", file=sys.stderr)
    for error in report.errors:
        print(f"  error: {error}", file=sys.stderr)
    if report.errors and report.added == 0:
        raise typer.Exit(1)


def main() -> None:
    """Console-script entry for ``soju-import``."""
    app(prog_name="soju-import")
