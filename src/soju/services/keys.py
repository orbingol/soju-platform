# SPDX-License-Identifier: BSD-3-Clause
"""Plugin-aware identity/dedup keys for the service layer.

Composes the pure key shapes from :mod:`soju.core.text` with normalization from
the active target- and base-language plugins. Repositories in
:mod:`soju.registry` receive these callables via dependency injection so the
data-access layer never reaches into a language plugin itself.
"""

from __future__ import annotations

from soju.base import get_base_language
from soju.core.text import example_key as _compose_example_key
from soju.core.text import sense_key as _compose_sense_key
from soju.languages import get_language

__all__ = ["example_key", "match_gloss", "normalize_term", "sense_key"]


def normalize_term(text: str) -> str:
    """Normalize a target-language term via the active language plugin."""
    return get_language().normalize(text)


def match_gloss(text: str) -> str:
    """Return a case-insensitive base-gloss identity key (normalize + casefold)."""
    return get_base_language().normalize(text).casefold()


def sense_key(hangul: str, english: str) -> tuple[str, str]:
    """Registry sense key: normalized term + normalized, casefolded gloss.

    Args:
        hangul: Raw target term.
        english: Raw base gloss / meaning.

    Returns:
        The ``(term, gloss)`` sense key used for registry uniqueness.
    """
    return _compose_sense_key(
        get_language().normalize(hangul),
        get_base_language().normalize_gloss(english),
    )


def example_key(hangul: str, english: str) -> tuple[str, str]:
    """Example dedup key: normalized target sentence + normalized gloss.

    Args:
        hangul: Raw target-language example sentence.
        english: Raw base-language gloss sentence.

    Returns:
        The ``(term, gloss)`` dedup key for example merges.
    """
    return _compose_example_key(
        get_language().normalize(hangul),
        get_base_language().normalize(english),
    )
