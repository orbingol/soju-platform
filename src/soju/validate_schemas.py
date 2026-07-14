# SPDX-License-Identifier: BSD-3-Clause
"""Run check-jsonschema over all canonical data files (manifest-driven paths)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from soju.db import data_root, glob_validate_targets


def _schema_dir(root: Path | None = None) -> Path:
    """Resolve ``data/schemas`` (colocated with the data root, else ``cwd/data/schemas``)."""
    colocated = data_root(root) / "schemas"
    if colocated.is_dir():
        return colocated
    return Path.cwd() / "data" / "schemas"


SCHEMA_FILES: dict[str, str] = {
    "registry-types": "registry_types.schema.json",
    "registry-vocabulary": "registry_vocabulary.schema.json",
    "examples-vocabulary": "examples_vocabulary.schema.json",
    "words-table": "words_table.schema.json",
    "topics-manifest": "topics_manifest.schema.json",
    "topics-table": "topics_table.schema.json",
    "topics-topics": "topics_topic.schema.json",
    "verb-manifest": "verb_manifest.schema.json",
    "verb-table": "verb_table.schema.json",
    "verb-forms": "verbs_forms.schema.json",
    "verb-constructions": "verbs_construction.schema.json",
    "grammar-manifest": "grammar_manifest.schema.json",
    "grammar-patterns": "grammar_pattern.schema.json",
    "staging-vocabulary": "staging_vocabulary.schema.json",
    "staging-exercises": "staging_exercises.schema.json",
    "staging-stories": "staging_stories.schema.json",
}


def validate_schemas(root: Path | None = None) -> list[str]:
    targets = glob_validate_targets(root)
    errors: list[str] = []
    schema_dir = _schema_dir(root)

    for name, files in targets.items():
        schema_name = SCHEMA_FILES.get(name)
        if schema_name is None:
            errors.append(f"{name}: no schema mapping configured")
            continue

        schema_path = schema_dir / schema_name
        if not schema_path.is_file():
            errors.append(f"{name}: missing schema file {schema_path}")
            continue

        existing = [path for path in files if Path(path).is_file()]
        missing = [path for path in files if not Path(path).is_file()]
        for path in missing:
            errors.append(f"{name}: missing data file {path}")

        if not existing:
            continue

        result = subprocess.run(
            [
                "check-jsonschema",
                "--schemafile",
                str(schema_path),
                "--base-uri",
                f"{schema_path.parent.as_uri()}/",
                *existing,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stdout + result.stderr).strip() or f"exit {result.returncode}"
            errors.append(f"{name}:\n{detail}")

    return errors


def main() -> None:
    errors = validate_schemas()
    if errors:
        print("Schema validation failed:", file=sys.stderr)
        for block in errors:
            print(block, file=sys.stderr)
            print(file=sys.stderr)
        sys.exit(1)
    print("Schema validation passed.")


if __name__ == "__main__":
    main()
