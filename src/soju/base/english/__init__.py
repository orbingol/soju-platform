# SPDX-License-Identifier: BSD-3-Clause
"""English base-language plugin package."""

from soju.base.english.plugin import EnglishBase, get_english_base
from soju.base.english.quality import is_bad_english, is_bare_english, strip_example_english
from soju.base.english.text import normalize_english, normalize_english_gloss

# Importing this package registers EnglishBase via plugin.py side effects.
__all__ = [
    "EnglishBase",
    "get_english_base",
    "is_bad_english",
    "is_bare_english",
    "normalize_english",
    "normalize_english_gloss",
    "strip_example_english",
]
