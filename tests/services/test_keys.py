# SPDX-License-Identifier: BSD-3-Clause
"""Plugin-aware key builders in the service layer."""

from __future__ import annotations

from soju.services.keys import example_key, match_gloss, normalize_term, sense_key


def test_normalize_term_uses_active_language() -> None:
    assert normalize_term("  학교  ") == "학교"


def test_sense_key_normalizes_and_casefolds_gloss() -> None:
    key = sense_key("  학교 ", "School")
    assert key == ("학교", "school")


def test_example_key_normalizes_both_sides() -> None:
    key = example_key(" 학교에 가요. ", "  I go   to school. ")
    assert key == ("학교에 가요.", "I go to school.")


def test_match_gloss_is_casefolded_normalized_english() -> None:
    assert match_gloss("  Good  Morning ") == "good morning"
