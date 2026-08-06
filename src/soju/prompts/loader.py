# SPDX-License-Identifier: BSD-3-Clause
"""Load shipped ``prompts.yaml`` (optional deep-merge override)."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

import yaml

from soju.prompts.models import PromptsSettings

PROMPTS_RESOURCE = "prompts.yaml"
PROMPTS_PACKAGE = "soju.backend.config.files"


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Prompts config must be a mapping, got {type(data).__name__}: {path}")
    return data


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


def _read_shipped_prompts_yaml() -> dict[str, Any]:
    with as_file(files(PROMPTS_PACKAGE).joinpath(PROMPTS_RESOURCE)) as resolved:
        return _read_yaml_mapping(Path(resolved))


def load_prompts(*, override: dict[str, Any] | None = None, path: Path | str | None = None) -> PromptsSettings:
    """Load :class:`PromptsSettings` from the shipped YAML, optionally merged with overrides.

    Args:
        override: Optional mapping under the ``prompts`` key (or the prompts body itself).
        path: Optional YAML file to merge after the shipped defaults (e.g. tests).

    Returns:
        Validated prompts settings.
    """
    data = _read_shipped_prompts_yaml()
    body = data.get("prompts", data)
    if not isinstance(body, dict):
        raise ValueError("prompts.yaml must contain a mapping under 'prompts' (or at the root)")
    if path is not None:
        extra = _read_yaml_mapping(Path(path).expanduser())
        extra_body = extra.get("prompts", extra)
        if not isinstance(extra_body, dict):
            raise ValueError(f"Prompts override must be a mapping: {path}")
        body = deep_merge(body, extra_body)
    if override:
        body = deep_merge(body, override)
    return PromptsSettings.model_validate(body)


@lru_cache(maxsize=1)
def get_prompts() -> PromptsSettings:
    """Cached shipped prompts (no user override). Clear with ``get_prompts.cache_clear()`` in tests."""
    return load_prompts()
