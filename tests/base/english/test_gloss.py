# SPDX-License-Identifier: BSD-3-Clause
"""Snapshot pins for English gloss / tense shaping."""

from __future__ import annotations

import pytest

from soju.base.english.gloss import _english_clause, english_for_tense

# Representative gloss × tense snapshots (byte-identical across the Phase-4a move).
ENGLISH_FOR_TENSE_CASES: list[tuple[str, str, str | None, str]] = [
    ("to eat", "present", None, "I eat."),
    ("to eat", "past", None, "I ate."),
    ("to eat", "future", None, "I will eat."),
    ("to go", "past", None, "I went."),
    ("to study Korean", "past", None, "I studied Korean."),
    ("to not know", "past", None, "I did not know."),
    ("to wash (hands)", "present", "씻다", "I wash my hands."),
    ("to see", "past", "보다", "I watched a movie."),
    ("to frolic", "past", None, "I froliced."),  # naive fallback
    ("to frolic", "future", None, "I will frolic."),
    ("to frolic", "present", None, "I frolic."),
]

ENGLISH_CLAUSE_CASES: list[tuple[str, str, str]] = [
    ("to eat", "present", "I eat."),
    ("to eat", "past", "I eated."),  # naive +ed (intentional)
    ("to eat", "future", "I will eat."),
    ("to study", "past", "I studied."),
    ("to be happy", "present", "I am happy."),
    ("to be happy", "past", "I was happy."),
    ("to be happy", "future", "I will be happy."),
    ("to try", "past", "I tried."),
]


@pytest.mark.parametrize(("gloss", "tense", "hangul", "expected"), ENGLISH_FOR_TENSE_CASES)
def test_english_for_tense_snapshots(gloss: str, tense: str, hangul: str | None, expected: str) -> None:
    assert english_for_tense(gloss, tense, hangul=hangul) == expected


@pytest.mark.parametrize(("gloss", "tense", "expected"), ENGLISH_CLAUSE_CASES)
def test_english_clause_snapshots(gloss: str, tense: str, expected: str) -> None:
    assert _english_clause(gloss, tense) == expected


def test_clause_for_tense_matches_english_for_tense() -> None:
    from soju.base.plugins import get_base_language

    bl = get_base_language("en")
    assert bl.clause_for_tense("to eat", "past") == english_for_tense("to eat", "past")
