# SPDX-License-Identifier: BSD-3-Clause
"""Speech request helpers."""

from __future__ import annotations

import pytest

pytest.importorskip("pydantic")

from soju.backend.models.speech import SpeechRequest, resolve_text, resolve_voice


def test_resolve_text_from_input_string() -> None:
    assert resolve_text(SpeechRequest(input="  안녕  ")) == "안녕"


def test_resolve_text_from_input_list() -> None:
    assert resolve_text(SpeechRequest(input=["안녕", "", "하세요"])) == "안녕\n하세요"


def test_resolve_text_from_text_field() -> None:
    assert resolve_text(SpeechRequest(text="  hi  ")) == "hi"


def test_resolve_voice_prefers_voice_then_model() -> None:
    assert resolve_voice(SpeechRequest(voice="v1", model="m1"), "default") == "v1"
    assert resolve_voice(SpeechRequest(model="m1"), "default") == "m1"
    assert resolve_voice(SpeechRequest(), "default") == "default"
