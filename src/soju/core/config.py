# SPDX-License-Identifier: BSD-3-Clause
"""Data-directory path resolution for Soju tooling."""

from __future__ import annotations

import os
from pathlib import Path


def data_root(root: Path | None = None) -> Path:
    """Resolve the data directory (``DATA_DIR`` env, else ``cwd/data``).

    Args:
        root: Optional explicit data-root override.

    Returns:
        Path to the data directory.
    """
    if root is not None:
        return root
    env = os.environ.get("DATA_DIR")
    if env:
        return Path(env)
    return Path.cwd() / "data"


def content_root(root: Path | None = None) -> Path:
    """Return ``<data_root>/content``.

    Args:
        root: Optional explicit data-root override.

    Returns:
        Path to the content tree.
    """
    return data_root(root) / "content"


def staging_root(root: Path | None = None) -> Path:
    """Return ``<data_root>/staging``.

    Args:
        root: Optional explicit data-root override.

    Returns:
        Path to the staging tree.
    """
    return data_root(root) / "staging"


def schema_rel_for(path: Path, schema_name: str, root: Path | None = None) -> str:
    """Relative ``$schema`` path from a YAML file under ``data/`` to ``data/schemas/``.

    Args:
        path: YAML file path under the data root.
        schema_name: Schema filename (e.g. ``registry_vocabulary.schema.json``).
        root: Optional explicit data-root override.

    Returns:
        A relative path string suitable for a yaml-language-server ``$schema`` comment.
    """
    rel = path.resolve().relative_to(data_root(root).resolve())
    # Climb to ``data/`` (exclude the filename), then into ``schemas/``.
    ups = "/".join([".."] * (len(rel.parts) - 1)) or "."
    return f"{ups}/schemas/{schema_name}"
