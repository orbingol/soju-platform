# SPDX-License-Identifier: BSD-3-Clause
"""Load and merge Soju backend YAML configuration."""

from __future__ import annotations

from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

import yaml

from soju.backend.config.settings import BackendSettings

DEFAULT_CONFIG_RESOURCE = "default_config.yaml"
CONFIG_FILES_PACKAGE = "soju.backend.config.files"


def user_config_path() -> Path:
    """Return the standard user config path (``~/.config/soju/backend.yaml``)."""
    return Path.home() / ".config" / "soju" / "backend.yaml"


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    """Load a YAML file and require a top-level mapping (or empty)."""
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Backend config must be a mapping, got {type(data).__name__}: {path}")
    return data


def _read_default_yaml() -> dict[str, Any]:
    """Load shipped defaults from package data under ``config/files/``."""
    with as_file(files(CONFIG_FILES_PACKAGE).joinpath(DEFAULT_CONFIG_RESOURCE)) as resolved:
        return _read_yaml_mapping(Path(resolved))


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Return a deep merge of ``override`` onto ``base`` (dicts recurse; other values replace)."""
    merged = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = deep_merge(existing, value)
        else:
            merged[key] = value
    return merged


def resolve_config_path(path: Path | str | None = None) -> Path | None:
    """Resolve the YAML override path.

    Search order:
    1. Explicit ``path`` (``--config``) when provided
    2. ``~/.config/soju/backend.yaml`` when that file exists
    3. ``None`` — caller uses packaged defaults only
    """
    if path is not None:
        return Path(path).expanduser()
    candidate = user_config_path()
    if candidate.is_file():
        return candidate
    return None


def load_settings(path: Path | str | None = None) -> BackendSettings:
    """Load :class:`BackendSettings` from packaged defaults merged with an optional override.

    Args:
        path: Explicit YAML override (``--config``). When omitted, uses
            ``~/.config/soju/backend.yaml`` if present; otherwise packaged defaults only.

    Returns:
        Validated backend settings.

    Raises:
        FileNotFoundError: If an explicit ``path`` does not exist.
        ValueError: If a YAML file is not a mapping.
        ValidationError: If merged data fails pydantic validation.
    """
    data = _read_default_yaml()
    override_path = resolve_config_path(path)
    if override_path is not None:
        if not override_path.is_file():
            raise FileNotFoundError(f"Backend config not found: {override_path}")
        data = deep_merge(data, _read_yaml_mapping(override_path))
    return BackendSettings.model_validate(data)
