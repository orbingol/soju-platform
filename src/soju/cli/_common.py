# SPDX-License-Identifier: BSD-3-Clause
"""Shared Typer helpers for Soju console scripts."""

from __future__ import annotations

from typing import Any

import typer


def make_app(**kwargs: Any) -> typer.Typer:
    """Create a Typer app with argparse-compatible help flags and no Rich chrome."""
    defaults: dict[str, Any] = {
        "add_completion": False,
        "rich_markup_mode": None,
        "pretty_exceptions_enable": False,
        "context_settings": {"help_option_names": ["-h", "--help"]},
    }
    defaults.update(kwargs)
    return typer.Typer(**defaults)


def flag(*param_decls: str, help: str | None = None) -> Any:
    """Boolean ``store_true``-style option (no ``--no-*`` counterpart).

    Pass an explicit positive name (e.g. ``"--dry-run"``) so Typer does not
    invent ``--no-dry-run``. Use as ``Annotated[bool, flag(\"--dry-run\")] = False``.
    """
    return typer.Option(*param_decls, help=help)
