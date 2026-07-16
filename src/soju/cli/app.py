# SPDX-License-Identifier: BSD-3-Clause
"""Root Typer app mounting all Soju subcommands (optional unified ``soju`` entry)."""

from __future__ import annotations

import os
from typing import Annotated, Optional

import typer

from soju.cli import examples as examples_cli
from soju.cli import promote as promote_cli
from soju.cli import translate as translate_cli
from soju.cli import validate as validate_cli
from soju.cli import verbs as verbs_cli
from soju.cli import words as words_cli
from soju.cli._common import flag, make_app
from soju.core.logging import ENV_ENABLED, configure_logging
from soju.languages.plugins import DEFAULT_LANGUAGE, ENV_LANGUAGE

app = make_app(
    name="soju",
    help="Soju Korean language learning platform CLI.",
    no_args_is_help=True,
)


@app.callback()
def _root(
    language: Annotated[
        Optional[str],
        typer.Option(
            "--language",
            "-L",
            help=f"Target language plugin code (default: ${ENV_LANGUAGE} or {DEFAULT_LANGUAGE})",
        ),
    ] = None,
    verbose: Annotated[bool, flag("--verbose", help="Enable verbose logging")] = False,
) -> None:
    """Global options shared by the unified ``soju`` entry point."""
    if language:
        os.environ[ENV_LANGUAGE] = language
    if verbose:
        os.environ[ENV_ENABLED] = "true"
        configure_logging(force=True)


app.add_typer(words_cli.app, name="import")
app.command("promote")(promote_cli.promote)
app.command("align")(validate_cli.align)
app.command("registry")(validate_cli.registry)
app.command("validate-schemas")(validate_cli.schemas)
app.command("fill-verbs")(verbs_cli.fill_verbs_cmd)
app.command("fill-examples")(examples_cli.fill_examples_cmd)
app.command("translate-words")(translate_cli.translate)


def import_main() -> None:
    """Console-script entry for ``soju-import`` (words/verbs subgroup)."""
    words_cli.main()


def main() -> None:
    """Optional unified ``soju`` console-script entry."""
    app(prog_name="soju")
