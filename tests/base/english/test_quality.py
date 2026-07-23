# SPDX-License-Identifier: BSD-3-Clause
"""English gloss quality helpers."""

from __future__ import annotations

from soju.base.english.quality import is_bad_english, is_bare_english, strip_example_english


def test_is_bad_english_broken_past() -> None:
    assert is_bad_english("I eated rice.", tense="past") is True
    assert is_bad_english("I ate rice.", tense="past") is False


def test_is_bare_english() -> None:
    assert is_bare_english("I talked.") is True
    assert is_bare_english("I talked with a friend yesterday.") is False


def test_strip_example_english() -> None:
    assert strip_example_english("Hello (formal).") == "Hello."


def test_is_acceptable_gloss_via_base() -> None:
    from soju.base.plugins import get_base_language

    bl = get_base_language("en")
    assert bl.is_acceptable_gloss("I ate rice.", tense="past") is True
    assert bl.is_acceptable_gloss("I eated rice.", tense="past") is False
    assert bl.scrub_example_gloss("Hi (casual).") == "Hi."
