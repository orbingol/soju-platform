# SPDX-License-Identifier: BSD-3-Clause
"""English :class:`~soju.base.contract.BaseLanguage` implementation."""

from __future__ import annotations

from soju.base.english import gloss, quality, text
from soju.base.plugins import register


class EnglishBase:
    """English base language: normalize glosses, shape tense clauses, quality checks."""

    code = "en"
    name = "English"

    def normalize(self, text_value: str) -> str:
        """Normalize English text for identity/dedup."""
        return text.normalize_english(text_value)

    def normalize_gloss(self, text_value: str) -> str:
        """Normalize a vocabulary meaning (lowercase + proper-name caps)."""
        return text.normalize_english_gloss(text_value)

    def scrub_example_gloss(self, text_value: str) -> str:
        """Strip parenthetical register notes from an example gloss."""
        return quality.strip_example_english(text_value)

    def clause_for_tense(self, gloss_value: str, tense: str, *, term: str | None = None) -> str:
        """Convert a dictionary gloss into a tensed ``I …`` clause."""
        return gloss.english_for_tense(gloss_value, tense, hangul=term)

    def is_acceptable_gloss(self, text_value: str, *, tense: str | None = None) -> bool:
        """Return True when the gloss passes English quality gates."""
        return not quality.is_bad_english(text_value, tense) and not quality.is_bare_english(text_value)


def get_english_base() -> EnglishBase:
    """Return the singleton English base-language instance."""
    return _ENGLISH_BASE


_ENGLISH_BASE = EnglishBase()
register(_ENGLISH_BASE)
