# SPDX-License-Identifier: BSD-3-Clause
"""Script-agnostic key composition and import-line parsing.

This module is a pure leaf: it depends only on the standard library. It never
reaches into a language plugin. Language-specific normalization is supplied by
callers — services resolve the active plugins and either pass normalized values
into these composition helpers or use the plugin-aware builders in
:mod:`soju.services.keys`.
"""

from __future__ import annotations

import re

IMPORT_LINE = re.compile(r"^(?P<entry>.*?)(?:\s*[\(（](?P<example>.*?)[\)）])?\s*$")

__all__ = [
    "IMPORT_LINE",
    "example_key",
    "parse_import_line",
    "sense_key",
]


def example_key(term_norm: str, gloss_norm: str) -> tuple[str, str]:
    """Compose an example dedup key from already-normalized parts.

    Args:
        term_norm: Target-language sentence, already normalized by the active
            language plugin.
        gloss_norm: Base-language gloss sentence, already normalized by the
            active base language.

    Returns:
        ``(term_norm, gloss_norm)``.
    """
    return term_norm, gloss_norm


def sense_key(term_norm: str, gloss_norm: str) -> tuple[str, str]:
    """Compose a registry sense key from already-normalized parts.

    The gloss is casefolded so that sense identity is case-insensitive.

    Args:
        term_norm: Target term, already normalized by the active language plugin.
        gloss_norm: Base gloss / meaning, already normalized by the active base
            language.

    Returns:
        ``(term_norm, gloss_norm.casefold())``.
    """
    return term_norm, gloss_norm.casefold()


def parse_import_line(line: str) -> tuple[str, str | None] | None:
    """Parse a plain-text import line into ``(entry, optional_example)``.

    Args:
        line: One line from a word list (``entry`` or ``entry (example)``).

    Returns:
        ``(entry, example_or_None)``, or ``None`` for blank/comment lines.
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    match = IMPORT_LINE.match(stripped)
    if not match:
        return None
    entry = match.group("entry").strip()
    example = match.group("example")
    if example is not None:
        example = example.strip()
    if not entry:
        return None
    return entry, example or None
