# SPDX-License-Identifier: BSD-3-Clause
"""Base-language plugin resolver."""

from __future__ import annotations

import os

from soju.base.contract import BaseLanguage

ENV_BASE_LANGUAGE = "SOJU_BASE_LANGUAGE"
DEFAULT_BASE_LANGUAGE = "en"

_REGISTRY: dict[str, BaseLanguage] = {}


def register(base: BaseLanguage) -> None:
    """Register a base-language implementation under ``base.code``."""
    _REGISTRY[base.code] = base


def _ensure_builtins_loaded() -> None:
    """Import built-in base languages so they self-register."""
    if DEFAULT_BASE_LANGUAGE not in _REGISTRY:
        import soju.base.english  # noqa: F401


def get_base_language(code: str | None = None) -> BaseLanguage:
    """Return the base language for ``code`` (default from env / ``en``).

    Args:
        code: Language code, or ``None`` to use ``SOJU_BASE_LANGUAGE`` / ``en``.

    Returns:
        The registered :class:`~soju.base.contract.BaseLanguage`.

    Raises:
        KeyError: If ``code`` is not registered.
    """
    _ensure_builtins_loaded()
    chosen = (code if code is not None else os.environ.get(ENV_BASE_LANGUAGE) or DEFAULT_BASE_LANGUAGE).strip()
    if chosen not in _REGISTRY:
        known = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise KeyError(f"Unknown base language {chosen!r}. Known: {known}")
    return _REGISTRY[chosen]
