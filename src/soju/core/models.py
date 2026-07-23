# SPDX-License-Identifier: BSD-3-Clause
"""Shared typed shapes and tense/variant constants.

On-disk schemas keep the legacy keys ``hangul`` (target term) and ``english``
(base gloss); names here mirror that layout until a future data migration.
"""

from __future__ import annotations

from typing import TypedDict

# Consolidated from db.EXAMPLE_* and the duplicated TENSES/VARIANTS in
# fill_examples / local_examples.
EXAMPLE_TENSES = ("present", "past", "future")
EXAMPLE_VARIANTS = ("casual_polite", "formal_polite")

TenseForms = dict[str, dict[str, str]]


class Example(TypedDict):
    """A target/base example sentence pair."""

    hangul: str
    english: str


class VocabularyEntry(TypedDict, total=False):
    """A vocabulary registry row (legacy hangul/english key names)."""

    id: str
    hangul: str
    romanization: str
    english: str
    type: str
    level: str
    visibility: str
    grammar_pattern: str
