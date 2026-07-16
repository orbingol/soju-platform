# SPDX-License-Identifier: BSD-3-Clause
"""``soju-fill-verbs`` console script."""

from __future__ import annotations

import sys
from typing import Annotated

import typer

from soju.cli._common import flag, make_app
from soju.services.verbs_fill import fill_verbs

app = make_app()


@app.command()
def fill_verbs_cmd(
    dry_run: Annotated[bool, flag("--dry-run")] = False,
    fill_empty: Annotated[
        bool,
        flag(
            "--fill-empty",
            help="Only fill missing forms/examples; leave existing entries unchanged",
        ),
    ] = False,
    strict: Annotated[
        bool,
        flag(
            "--strict",
            help="Exit non-zero when no verbs were updated (useful in automation)",
        ),
    ] = False,
) -> None:
    """Generate verb forms and examples for registry verbs."""
    try:
        counts = fill_verbs(dry_run=dry_run, fill_empty=fill_empty)
    except (OSError, ValueError, TypeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise typer.Exit(1) from exc

    mode = "would fill" if dry_run else "filled"
    print(f"{mode} forms/examples for {counts['filled_forms']}/{counts['verbs']} verbs (examples={counts['filled_examples']}, skipped={counts['skipped']}).")
    if strict and counts["filled_forms"] == 0 and counts["verbs"] > 0:
        print("Error: --strict and nothing was filled.", file=sys.stderr)
        raise typer.Exit(1)


def fill_main() -> None:
    """Console-script entry for ``soju-fill-verbs``."""
    app(prog_name="soju-fill-verbs")
