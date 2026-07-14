# SPDX-License-Identifier: BSD-3-Clause
"""Heuristic conjugation helpers."""

from __future__ import annotations

from soju.conjugate import conjugate_verb, example_for_form


def test_conjugate_known_root_먹다() -> None:
    forms = conjugate_verb("먹다")
    assert forms["present"]["casual_polite"] == "먹어요"
    assert forms["present"]["formal_polite"] == "먹습니다"
    assert "past" in forms and "future" in forms


def test_conjugate_hada_compound() -> None:
    forms = conjugate_verb("공부하다")
    assert forms["present"]["casual_polite"] == "공부해요"
    assert forms["present"]["formal_polite"] == "공부합니다"


def test_example_for_form_structure() -> None:
    forms = conjugate_verb("먹다")
    form = forms["present"]["casual_polite"]
    example = example_for_form("먹다", form, "to eat", tense="present")
    assert "hangul" in example and "english" in example
    assert form in example["hangul"] or "먹" in example["hangul"]
