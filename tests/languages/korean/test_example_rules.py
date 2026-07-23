# SPDX-License-Identifier: BSD-3-Clause
"""Korean example-sentence form rules."""

from __future__ import annotations

import pytest

from soju.languages.plugins import get_language
from soju.languages.korean.example_rules import embedded_form_hint, form_in_sentence


@pytest.mark.parametrize(
    ("form", "sentence", "ok"),
    [
        ("샤워해요", "오늘 샤워해요.", True),
        ("먹어요", "저는 밥을 먹어요.", True),
        ("회사에 가요", "내일 회사에 가요.", True),
        ("먹어요", "좋아요.", False),
        ("씻어요", "아침에 샤워해요.", True),  # synonym alternate
    ],
)
def test_form_in_sentence_cases(form: str, sentence: str, ok: bool) -> None:
    assert form_in_sentence(form, sentence) is ok


def test_form_in_sentence_via_plugin() -> None:
    assert get_language("ko").form_in_sentence("샤워해요", "오늘 샤워해요.") is True


def test_embedded_form_hint_for_prefixed_forms() -> None:
    forms = {
        "present": {"casual_polite": "학교에 가요", "formal_polite": "학교에 갑니다"},
        "past": {"casual_polite": "학교에 갔어요", "formal_polite": "학교에 갔습니다"},
        "future": {"casual_polite": "학교에 갈 거예요", "formal_polite": "학교에 가겠습니다"},
    }
    hint = embedded_form_hint(forms)
    assert hint is not None
    assert "학교에" in hint

    simple = {
        "present": {"casual_polite": "가요", "formal_polite": "갑니다"},
        "past": {"casual_polite": "갔어요", "formal_polite": "갔습니다"},
        "future": {"casual_polite": "갈 거예요", "formal_polite": "가겠습니다"},
    }
    assert embedded_form_hint(simple) is None
