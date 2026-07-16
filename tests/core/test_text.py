# SPDX-License-Identifier: BSD-3-Clause
"""Pure key composition and import-line parsing (no plugin dependency)."""

from __future__ import annotations

from soju.core.text import example_key, parse_import_line, sense_key


def test_sense_key_casefolds_gloss_only() -> None:
    # Inputs are already normalized; sense_key only casefolds the gloss.
    key = sense_key("학교", "School")
    assert key == ("학교", "school")


def test_example_key_is_verbatim_composition() -> None:
    key = example_key("학교에 가요.", "I go to School.")
    assert key == ("학교에 가요.", "I go to School.")


def test_parse_import_line() -> None:
    parsed = parse_import_line("학교 (I go to school)")
    assert parsed is not None
    entry, example = parsed
    assert entry == "학교"
    assert example == "I go to school"
    assert parse_import_line("# comment") is None
