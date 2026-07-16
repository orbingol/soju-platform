# SPDX-License-Identifier: BSD-3-Clause
"""Validation console scripts: align, registry, validate-schemas."""

from __future__ import annotations

import sys

import typer

from soju.cli._common import make_app
from soju.core.yaml_io import load_yaml
from soju.registry.verbs import verb_table_path
from soju.registry.vocabulary import vocabulary_by_type
from soju.services.validation.alignment import validate_alignment
from soju.services.validation.registry_checks import validate_registry
from soju.services.validation.schemas import validate_schemas

align_app = make_app()
registry_app = make_app()
schemas_app = make_app()


@align_app.command()
def align() -> None:
    """Validate verb forms and examples against table layout."""
    table = load_yaml(verb_table_path())
    verbs = vocabulary_by_type("verb")

    if not isinstance(table, dict):
        print("content/verbs/table.yaml must be a mapping.", file=sys.stderr)
        raise typer.Exit(1)

    errors = validate_alignment(table, verbs)
    if errors:
        print("Verb data alignment errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise typer.Exit(1)

    print("Verb data alignment OK.")


@registry_app.command()
def registry() -> None:
    """Validate vocabulary registry, types, and topic refs."""
    errors = validate_registry()
    if errors:
        print("Registry validation errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise typer.Exit(1)

    print("Registry validation OK.")


@schemas_app.command()
def schemas() -> None:
    """Run check-jsonschema over all canonical data files."""
    errors = validate_schemas()
    if errors:
        print("Schema validation failed:", file=sys.stderr)
        for block in errors:
            print(block, file=sys.stderr)
            print(file=sys.stderr)
        raise typer.Exit(1)
    print("Schema validation passed.")


def align_main() -> None:
    """Console-script entry for ``soju-align``."""
    align_app(prog_name="soju-align")


def registry_main() -> None:
    """Console-script entry for ``soju-registry``."""
    registry_app(prog_name="soju-registry")


def schemas_main() -> None:
    """Console-script entry for ``soju-validate-schemas``."""
    schemas_app(prog_name="soju-validate-schemas")
