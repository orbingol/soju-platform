# SPDX-License-Identifier: BSD-3-Clause
"""Pure examples_fill helpers and local/LLM fill paths (fake LLM)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from soju.languages import get_language
from soju.levels import get_language_level
from soju.llm.base import LlmError
from soju.llm.jsonutil import parse_json_content
from soju.registry.examples import load_examples_store
from soju.registry.verbs import load_verb_forms
from soju.services.examples_fill.generate import (
    _chat_json,
    generate_noun_batch,
    generate_verb_batch,
    parse_verb_batch_response,
)
from soju.services.examples_fill.service import dry_run_examples_preview, fill_examples
from soju.services.examples_fill.validate import (
    clean_example,
    diagnose_verb_examples,
    filter_nouns_for_fill_mode,
    filter_verbs_for_fill_mode,
    merge_verb_examples_from_response,
    missing_verb_cells,
    validate_noun_examples,
    validate_variant_examples,
)
from tests.constants import VERB_ID, WORD_ID


def _meokda_forms() -> dict[str, dict[str, str]]:
    return {
        "present": {"casual_polite": "먹어요", "formal_polite": "먹습니다"},
        "past": {"casual_polite": "먹었어요", "formal_polite": "먹었습니다"},
        "future": {"casual_polite": "먹을 거예요", "formal_polite": "먹겠습니다"},
    }


def _complete_verb_examples_payload(verb_id: str = VERB_ID) -> dict:
    forms = _meokda_forms()
    examples: dict = {}
    gloss = {
        "present": "I eat bibimbap for lunch.",
        "past": "I ate ramen with a friend yesterday.",
        "future": "I will eat cake on the weekend.",
    }
    for tense, variants in forms.items():
        examples[tense] = {}
        for variant, form in variants.items():
            examples[tense][variant] = [{"hangul": f"오늘 {form}.", "english": gloss[tense]}]
    return {"verbs": [{"id": verb_id, "examples": examples}]}


def test_clean_example_rejects_missing_fields() -> None:
    assert clean_example({}) is None
    assert clean_example({"hangul": "책"}) is None
    cleaned = clean_example({"hangul": "책이 있어요.", "english": "There is a book."})
    assert cleaned is not None
    assert cleaned["hangul"] == "책이 있어요."


def test_parse_json_content_strips_fences() -> None:
    raw = '```json\n{"records": []}\n```'
    parsed = parse_json_content(raw)
    assert parsed == {"records": []}


def test_validate_noun_examples_requires_hangul_in_sentence() -> None:
    assert (
        validate_noun_examples(
            [{"hangul": "좋아요.", "english": "It is good."}],
            "책",
            examples_per=1,
        )
        is None
    )
    cleaned = validate_noun_examples(
        [{"hangul": "책이 있어요.", "english": "There is a book."}],
        "책",
        examples_per=1,
    )
    assert cleaned is not None
    assert len(cleaned) == 1


def test_filter_modes(data_root: Path) -> None:
    store = load_examples_store(data_root)
    verbs = [({"id": VERB_ID, "hangul": "먹다"}, {"present": {}, "past": {}, "future": {}})]
    assert filter_verbs_for_fill_mode(verbs, store, fill_mode="refresh-all") == verbs
    nouns = [{"id": WORD_ID, "hangul": "학교"}]
    assert filter_nouns_for_fill_mode(nouns, store, fill_mode="refresh-all") == nouns
    assert filter_nouns_for_fill_mode(nouns, store, fill_mode="fill-empty") == []


def test_diagnose_and_merge_verb_helpers() -> None:
    forms = _meokda_forms()
    assert diagnose_verb_examples(forms, None) == ["model returned invalid examples object"]
    reasons = diagnose_verb_examples(forms, {"present": {}})
    assert any("past" in r for r in reasons)

    partial = merge_verb_examples_from_response(
        forms,
        _complete_verb_examples_payload()["verbs"][0]["examples"],
        {},
        examples_per=1,
    )
    assert missing_verb_cells(forms, partial) == []
    assert validate_variant_examples("먹어요", [{"hangul": "밥을 먹어요.", "english": "I eat rice at home."}], tense="present")


def test_fill_examples_local_refresh(data_root: Path) -> None:
    store, warnings, updated = fill_examples(
        llm=None,
        temperature=0.0,
        verb_batch_size=4,
        noun_batch_size=6,
        verbs=True,
        nouns=True,
        limit=None,
        clean_only=False,
        verbose=False,
        level_id="1A",
        local=True,
        examples_per=1,
        fill_mode="refresh-all",
        root=data_root,
    )
    assert updated >= 1
    assert VERB_ID in store
    assert "present" in store[VERB_ID]
    assert WORD_ID in store
    assert store[WORD_ID]["default"]


def test_fill_examples_clean_only(data_root: Path) -> None:
    from soju.registry.examples import save_examples_store

    store = load_examples_store(data_root)
    store[WORD_ID]["default"][0]["english"] = "I go to school. (formal)"
    save_examples_store(store, data_root)
    out, warnings, updated = fill_examples(
        llm=None,
        temperature=0.0,
        verb_batch_size=1,
        noun_batch_size=1,
        verbs=False,
        nouns=False,
        limit=None,
        clean_only=True,
        verbose=False,
        level_id="1A",
        root=data_root,
    )
    assert updated >= 1
    assert "(formal)" not in out[WORD_ID]["default"][0]["english"]


def test_dry_run_examples_preview(data_root: Path) -> None:
    text = dry_run_examples_preview(
        verbs=True,
        nouns=True,
        fill_mode="fill-empty",
        verb_batch_size=4,
        noun_batch_size=6,
        examples_per=1,
        level_id="1A",
        root=data_root,
    )
    assert "Language level:" in text
    assert "Fill mode: fill-empty" in text
    assert "Would generate 1 example(s) per variant" in text


def test_fill_examples_progress_callback(data_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    messages: list[str] = []
    store, warnings, updated = fill_examples(
        llm=None,
        temperature=0.0,
        verb_batch_size=4,
        noun_batch_size=6,
        verbs=True,
        nouns=False,
        limit=None,
        clean_only=False,
        verbose=False,
        level_id="1A",
        local=True,
        examples_per=1,
        fill_mode="refresh-all",
        root=data_root,
        progress=messages.append,
    )
    assert updated >= 1
    assert any("local templates" in msg for msg in messages)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_fill_examples_default_progress_silent(data_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    fill_examples(
        llm=None,
        temperature=0.0,
        verb_batch_size=4,
        noun_batch_size=6,
        verbs=True,
        nouns=False,
        limit=None,
        clean_only=False,
        verbose=False,
        level_id="1A",
        local=True,
        examples_per=1,
        fill_mode="refresh-all",
        root=data_root,
    )
    captured = capsys.readouterr()
    assert captured.err == ""


class _FakeLlm:
    def __init__(self, payload: dict | list | str) -> None:
        self.payload = payload
        self.calls = 0

    def chat(self, messages, **kwargs):  # noqa: ANN001
        self.calls += 1
        if isinstance(self.payload, str):
            return self.payload
        return json.dumps(self.payload, ensure_ascii=False)


def test_fill_examples_nouns_with_fake_llm(data_root: Path) -> None:
    payload = {
        "entries": [
            {
                "id": WORD_ID,
                "examples": [{"hangul": "학교에 가요.", "english": "I go to school today."}],
            }
        ]
    }
    llm = _FakeLlm(payload)
    store, warnings, updated = fill_examples(
        llm=llm,
        temperature=0.0,
        verb_batch_size=1,
        noun_batch_size=6,
        verbs=False,
        nouns=True,
        limit=1,
        clean_only=False,
        verbose=False,
        level_id="1A",
        examples_per=1,
        fill_mode="refresh-all",
        root=data_root,
    )
    assert updated == 1
    assert store[WORD_ID]["default"][0]["hangul"] == "학교에 가요."
    assert llm.calls >= 1


def test_fill_examples_verbs_with_fake_llm(data_root: Path) -> None:
    llm = _FakeLlm(_complete_verb_examples_payload())
    store, warnings, updated = fill_examples(
        llm=llm,
        temperature=0.0,
        verb_batch_size=4,
        noun_batch_size=1,
        verbs=True,
        nouns=False,
        limit=1,
        clean_only=False,
        verbose=False,
        level_id="1A",
        examples_per=1,
        fill_mode="refresh-all",
        root=data_root,
        max_attempts=1,
    )
    assert updated == 1
    assert "present" in store[VERB_ID]


def test_fill_examples_requires_llm_unless_local(data_root: Path) -> None:
    with pytest.raises(ValueError, match="llm is required"):
        fill_examples(
            llm=None,
            temperature=0.0,
            verb_batch_size=1,
            noun_batch_size=1,
            verbs=True,
            nouns=False,
            limit=1,
            clean_only=False,
            verbose=False,
            level_id="1A",
            local=False,
            root=data_root,
        )


def test_chat_json_and_batch_helpers(data_root: Path) -> None:
    forms = load_verb_forms(VERB_ID, data_root)
    verb = {"id": VERB_ID, "hangul": "먹다", "english": "to eat"}
    level = get_language_level("1A", data_root)
    lang = get_language()

    bad = _FakeLlm("not-json{{{")
    assert _chat_json(system="s", user="u", llm=bad, temperature=0.0, verbose=False) is None

    good = _FakeLlm(_complete_verb_examples_payload())
    parsed = _chat_json(system="s", user="u", llm=good, temperature=0.0, verbose=False)
    assert parsed is not None
    matched = parse_verb_batch_response(parsed, [(verb, forms)], examples_per=1)
    assert VERB_ID in matched

    noun_llm = _FakeLlm(
        {
            "entries": [
                {
                    "id": WORD_ID,
                    "examples": [{"hangul": "학교가 커요.", "english": "The school is big."}],
                }
            ]
        }
    )
    nouns = generate_noun_batch(
        [{"id": WORD_ID, "hangul": "학교", "english": "school"}],
        level=level,
        vocabulary_context="",
        llm=noun_llm,
        prompts=lang,
        temperature=0.0,
        verbose=False,
        examples_per=1,
    )
    assert WORD_ID in nouns

    class _Boom(_FakeLlm):
        def chat(self, messages, **kwargs):  # noqa: ANN001
            raise LlmError("down")

    with pytest.raises(LlmError):
        _chat_json(system="s", user="u", llm=_Boom({}), temperature=0.0, verbose=False)

    verb_llm = _FakeLlm(_complete_verb_examples_payload())
    verbs = generate_verb_batch(
        [(verb, forms)],
        level=level,
        vocabulary_context="",
        llm=verb_llm,
        prompts=lang,
        temperature=0.0,
        verbose=False,
        examples_per=1,
        max_attempts=1,
    )
    assert VERB_ID in verbs
