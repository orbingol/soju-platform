# SPDX-License-Identifier: BSD-3-Clause
"""Vocabulary type catalog loader."""

from __future__ import annotations

from pathlib import Path

from soju.core.config import content_root
from soju.core.yaml_io import load_yaml


def load_types(root: Path | None = None) -> list[dict]:
    """Load registry type definitions from ``content/registry/types.yaml``.

    Args:
        root: Optional data-root override.

    Returns:
        List of type mapping entries.

    Raises:
        ValueError: If the file shape is invalid.
    """
    data = load_yaml(content_root(root) / "registry" / "types.yaml")
    if not isinstance(data, dict):
        raise ValueError("content/registry/types.yaml must be a mapping.")
    types = data.get("types", [])
    if not isinstance(types, list):
        raise ValueError("content/registry/types.yaml types must be a list.")
    return types
