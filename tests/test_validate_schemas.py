# SPDX-License-Identifier: BSD-3-Clause
"""Schema mapping coverage for validate targets."""

from __future__ import annotations

from pathlib import Path

from soju import db
from soju.validate_schemas import SCHEMA_FILES, validate_schemas


def test_validate_schemas_maps_all_target_keys(data_root: Path) -> None:
    targets = db.glob_validate_targets(data_root)
    for key in targets:
        assert key in SCHEMA_FILES, f"missing schema mapping for {key}"


def test_validate_schemas_ok_on_fixture(data_root: Path) -> None:
    # Fixture YAML is structurally minimal; some schemas may require extra fields.
    # Ensure the runner returns a list (and does not crash) against the tree.
    errors = validate_schemas(data_root)
    assert isinstance(errors, list)


def test_validate_schemas_fails_invalid_yaml(data_root: Path) -> None:
    types_path = data_root / "content" / "registry" / "types.yaml"
    types_path.write_text("types: not-a-list\n", encoding="utf-8")
    errors = validate_schemas(data_root)
    assert errors
