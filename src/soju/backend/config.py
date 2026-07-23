# SPDX-License-Identifier: BSD-3-Clause
"""Load and merge Soju backend YAML configuration."""

from __future__ import annotations

import os
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

import yaml

from soju.backend.models.settings import BackendSettings

ENV_CONFIG_PATH = "SOJU_BACKEND_CONFIG"


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
    """Load shipped defaults from package data."""
    with as_file(files("soju.backend").joinpath("default_config.yaml")) as resolved:
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
    """Resolve an explicit config path or ``SOJU_BACKEND_CONFIG``; otherwise ``None`` (defaults only)."""
    if path is not None:
        return Path(path)
    env = os.environ.get(ENV_CONFIG_PATH)
    if env and env.strip():
        return Path(env.strip())
    return None


def load_settings(path: Path | str | None = None) -> BackendSettings:
    """Load :class:`BackendSettings` from shipped defaults merged with an optional override file.

    Args:
        path: Optional YAML override path. When omitted, uses ``$SOJU_BACKEND_CONFIG`` if set;
            otherwise package defaults only.

    Returns:
        Validated backend settings.

    Raises:
        FileNotFoundError: If an explicit or env config path does not exist.
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
