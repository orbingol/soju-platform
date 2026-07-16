# SPDX-License-Identifier: BSD-3-Clause
"""Target-language plugin resolver."""

from __future__ import annotations

import os

from soju.languages.contracts import LanguagePlugin

ENV_LANGUAGE = "SOJU_LANGUAGE"
DEFAULT_LANGUAGE = "ko"

_REGISTRY: dict[str, LanguagePlugin] = {}


def register(plugin: LanguagePlugin) -> None:
    """Register a target-language plugin under ``plugin.code``."""
    _REGISTRY[plugin.code] = plugin


def _ensure_builtins_loaded() -> None:
    """Import built-in target languages so they self-register."""
    if DEFAULT_LANGUAGE not in _REGISTRY:
        import soju.languages.korean.plugin  # noqa: F401


def get_language(code: str | None = None) -> LanguagePlugin:
    """Return the plugin for ``code`` (defaults to the active language).

    The active language is resolved from ``SOJU_LANGUAGE`` (env), falling back
    to ``"ko"``.

    Args:
        code: Language code, or ``None`` to use env / default.

    Returns:
        The registered :class:`~soju.languages.contracts.LanguagePlugin`.

    Raises:
        KeyError: If ``code`` is not registered.
    """
    _ensure_builtins_loaded()
    chosen = (code if code is not None else os.environ.get(ENV_LANGUAGE) or DEFAULT_LANGUAGE).strip()
    if chosen not in _REGISTRY:
        known = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise KeyError(f"Unknown language {chosen!r}. Known: {known}")
    return _REGISTRY[chosen]


def active_language() -> LanguagePlugin:
    """Return the active target language (from env / default)."""
    return get_language(None)
