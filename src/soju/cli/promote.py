# SPDX-License-Identifier: BSD-3-Clause
"""``soju-promote`` console script."""

from __future__ import annotations

import sys
from typing import Annotated

import typer

from soju.cli._common import flag, make_app
from soju.services.promote import promote_topic

app = make_app()


@app.command()
def promote(
    topic: Annotated[str, typer.Option("--topic", help="Topic id (e.g. family)")],
    dry_run: Annotated[bool, flag("--dry-run")] = False,
) -> None:
    """Promote local topic entries to registry."""
    try:
        counts = promote_topic(topic, dry_run=dry_run)
    except (KeyError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise typer.Exit(1) from exc

    mode = "would promote" if dry_run else "promoted"
    print(f"{mode} {counts['promoted']} entries; skipped {counts['skipped']}.")


def main() -> None:
    """Console-script entry for ``soju-promote``."""
    app(prog_name="soju-promote")
