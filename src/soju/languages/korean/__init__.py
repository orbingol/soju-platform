# SPDX-License-Identifier: BSD-3-Clause
"""Korean target-language plugin.

Keep this package init lightweight: ``soju.core.text`` imports
:mod:`soju.languages.korean.text` and must not pull conjugation / examples /
registry via a heavy ``__init__``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from soju.languages.korean.text import has_hangul, normalize_hangul

if TYPE_CHECKING:
    from soju.languages.korean.plugin import KoreanLanguage

__all__ = [
    "KoreanLanguage",
    "get_korean_language",
    "has_hangul",
    "normalize_hangul",
]


def __getattr__(name: str):
    if name in ("KoreanLanguage", "get_korean_language"):
        from soju.languages.korean.plugin import KoreanLanguage, get_korean_language

        if name == "KoreanLanguage":
            return KoreanLanguage
        return get_korean_language
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
