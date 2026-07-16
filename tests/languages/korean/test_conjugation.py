# SPDX-License-Identifier: BSD-3-Clause
"""Heuristic conjugation helpers."""

from __future__ import annotations

import pytest

from soju.languages.korean.conjugation import conjugate_verb, example_for_form, examples_for_verb


@pytest.mark.parametrize(
    ("hangul", "casual_present"),
    [
        ("먹다", "먹어요"),
        ("가다", "가요"),
        ("오다", "와요"),
        ("듣다", "들어요"),
        ("쓰다", "써요"),
        ("공부하다", "공부해요"),
        ("만나다", "만나요"),
        ("배우다", "배워요"),
        ("학교에 가다", "학교에 가요"),
    ],
)
def test_conjugate_known_roots(hangul: str, casual_present: str) -> None:
    forms = conjugate_verb(hangul)
    assert forms["present"]["casual_polite"] == casual_present
    assert forms["present"]["formal_polite"]
    assert forms["past"]["casual_polite"]
    assert forms["future"]["casual_polite"]


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


def test_examples_for_verb_covers_cells() -> None:
    forms = conjugate_verb("먹다")
    examples = examples_for_verb("먹다", "to eat", forms)
    assert set(examples) == {"present", "past", "future"}
    assert examples["present"]["casual_polite"][0]["hangul"]
