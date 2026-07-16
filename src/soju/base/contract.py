# SPDX-License-Identifier: BSD-3-Clause
"""Base-language (known-language) plugin contract."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class BaseLanguage(Protocol):
    """A learner's *known* language: normalization, gloss shaping, quality checks.

    Attributes:
        code: Short language code (e.g. ``"en"``).
        name: Human-readable name (e.g. ``"English"``).
    """

    code: str
    name: str

    def normalize(self, text: str) -> str:
        """Return ``text`` normalized for dedup/identity (e.g. trimming)."""

    def normalize_gloss(self, text: str) -> str:
        """Return a vocabulary meaning/gloss normalized for storage and sense keys."""

    def scrub_example_gloss(self, text: str) -> str:
        """Strip register notes / noise from an example sentence gloss."""

    def clause_for_tense(self, gloss: str, tense: str, *, term: str | None = None) -> str:
        """Convert a dictionary ``gloss`` into a tense-appropriate clause.

        Args:
            gloss: Dictionary gloss in the base language.
            tense: ``present``, ``past``, or ``future``.
            term: Optional target-language dictionary form for term-specific overrides.
        """

    def is_acceptable_gloss(self, text: str, *, tense: str | None = None) -> bool:
        """Return ``True`` if ``text`` is an acceptable gloss/sentence (quality gate)."""
