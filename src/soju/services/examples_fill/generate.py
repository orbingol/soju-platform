# SPDX-License-Identifier: BSD-3-Clause
"""LLM batch generation for vocabulary examples."""

from __future__ import annotations

import json
from typing import Any

from soju.core.logging import get_logger
from soju.core.models import EXAMPLE_TENSES as TENSES
from soju.core.models import EXAMPLE_VARIANTS as VARIANTS
from soju.languages import get_language
from soju.languages.contracts import PromptProvider
from soju.levels import LanguageLevel
from soju.llm.base import LlmClient, LlmError
from soju.llm.jsonutil import parse_json_content
from soju.registry.examples import verb_examples_complete
from soju.services.examples_fill.types import ProgressFn, noop_progress
from soju.services.examples_fill.validate import (
    diagnose_verb_examples,
    merge_verb_examples_from_response,
    missing_verb_cells,
    validate_noun_examples,
)

logger = get_logger(__name__)


def _verb_payload_item(verb: dict[str, Any], forms: dict[str, dict[str, str]]) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": verb["id"],
        "hangul": verb["hangul"],
        "english": verb["english"],
        "forms": forms,
    }
    hint = get_language().embedded_form_hint(forms)
    if hint:
        item["form_rule"] = hint
    return item


def _verb_user_message(
    batch: list[tuple[dict[str, Any], dict[str, dict[str, str]]]],
    *,
    examples_per: int,
    partial: dict[str, dict[str, dict[str, list[dict[str, str]]]]] | None = None,
) -> str:
    lines = [
        f"Generate {examples_per} distinct example(s) per tense/variant for these verbs.",
        "Each hangul value MUST contain the exact `forms` string for that tense/variant (copy it as a contiguous substring; you may add words before/after).",
    ]
    for verb, forms in batch:
        if not get_language().embedded_form_hint(forms):
            continue
        sample = forms.get("past", {}).get("casual_polite") or next(
            forms[t][v] for t in TENSES for v in VARIANTS if forms.get(t, {}).get(v)
        )
        lines.append(
            f'- {verb["hangul"]}: example past/casual_polite hangul = "어제 친구하고 {sample}." — '
            f'do NOT change {sample.rsplit(" ", 1)[0]!r} to another place.'
        )
        missing = missing_verb_cells(forms, (partial or {}).get(verb["id"], {}))
        if missing:
            need = ", ".join(f"{t}/{v}={form!r}" for t, v, form in missing[:6])
            lines.append(f"- {verb['hangul']}: still required cells: {need}")
    payload = {"verbs": [_verb_payload_item(verb, forms) for verb, forms in batch]}
    lines.append(json.dumps(payload, ensure_ascii=False, indent=2))
    return "\n".join(lines)


def _log_verb_rejections(
    parsed: Any,
    batch: list[tuple[dict[str, Any], dict[str, dict[str, str]]]],
    matched: dict[str, Any],
    *,
    examples_per: int,
    progress: ProgressFn,
) -> None:
    verbs = parsed.get("verbs") if isinstance(parsed, dict) else None
    if not isinstance(verbs, list):
        return
    by_id = {entry.get("id"): entry for entry in verbs if isinstance(entry, dict)}
    for verb, forms in batch:
        if verb["id"] in matched:
            continue
        entry = by_id.get(verb["id"])
        if not entry:
            progress(f"  rejected {verb['hangul']}: missing from model response")
            continue
        reasons = diagnose_verb_examples(forms, entry.get("examples"), examples_per=examples_per)
        if reasons:
            progress(f"  rejected {verb['hangul']}: {reasons[0]}")


def _chat_json(
    *,
    system: str,
    user: str,
    llm: LlmClient,
    temperature: float,
    verbose: bool,
    progress: ProgressFn | None = None,
) -> Any | None:
    log = progress or noop_progress
    logger.debug(
        "fill_examples calling LLM system_chars=%s user_chars=%s",
        len(system),
        len(user),
    )
    try:
        content = llm.chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            json_mode=True,
            temperature=temperature,
            num_predict=8192,
        )
    except LlmError:
        raise
    if verbose:
        log(content)
    try:
        parsed = parse_json_content(content)
    except json.JSONDecodeError:
        logger.debug("JSON parse failed content_head=%r", content[:300])
        log("  LLM returned unparseable JSON.")
        if verbose:
            log(content)
        return None
    top_keys = list(parsed.keys()) if isinstance(parsed, dict) else type(parsed).__name__
    logger.debug("JSON parsed top_keys=%s", top_keys)
    return parsed


def parse_verb_batch_response(
    parsed: Any,
    batch: list[tuple[dict[str, Any], dict[str, dict[str, str]]]],
    *,
    examples_per: int = 1,
    partial: dict[str, dict[str, dict[str, list[dict[str, str]]]]] | None = None,
) -> dict[str, dict[str, dict[str, list[dict[str, str]]]]]:
    expected = {verb["id"]: (verb, forms) for verb, forms in batch}
    results: dict[str, dict[str, dict[str, list[dict[str, str]]]]] = {}
    in_progress = dict(partial or {})

    verbs = parsed.get("verbs") if isinstance(parsed, dict) else None
    if not isinstance(verbs, list):
        return results

    for entry in verbs:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id")
        if entry_id not in expected:
            continue
        _, forms = expected[entry_id]
        merged = merge_verb_examples_from_response(
            forms,
            entry.get("examples"),
            in_progress.get(entry_id, {}),
            examples_per=examples_per,
        )
        in_progress[entry_id] = merged
        if verb_examples_complete(forms, merged):
            results[entry_id] = merged
    return results


def generate_verb_batch(
    batch: list[tuple[dict[str, Any], dict[str, dict[str, str]]]],
    *,
    level: LanguageLevel,
    vocabulary_context: str,
    llm: LlmClient,
    prompts: PromptProvider,
    temperature: float,
    verbose: bool,
    examples_per: int = 1,
    max_attempts: int = 3,
    progress: ProgressFn | None = None,
) -> dict[str, dict[str, dict[str, list[dict[str, str]]]]]:
    log = progress or noop_progress
    results: dict[str, dict[str, dict[str, list[dict[str, str]]]]] = {}
    partial: dict[str, dict[str, dict[str, list[dict[str, str]]]]] = {verb["id"]: {} for verb, _ in batch}

    for attempt in range(max(1, max_attempts)):
        pending = [(verb, forms) for verb, forms in batch if verb["id"] not in results]
        if not pending:
            break
        if attempt > 0:
            labels = ", ".join(verb["hangul"] for verb, _ in pending)
            log(f"  retry {attempt + 1}/{max_attempts}: {labels}")

        attempt_temp = max(0.1, temperature - (0.12 * attempt))
        parsed = _chat_json(
            system=prompts.verb_examples_system_prompt(level, vocabulary_context, examples_per=examples_per),
            user=_verb_user_message(
                pending,
                examples_per=examples_per,
                partial=partial,
            ),
            llm=llm,
            temperature=attempt_temp,
            verbose=verbose,
            progress=log,
        )
        if parsed is None:
            continue

        attempt_results = parse_verb_batch_response(
            parsed,
            pending,
            examples_per=examples_per,
            partial=partial,
        )
        for verb, forms in pending:
            vid = verb["id"]
            merged = partial.get(vid, {})
            if vid in attempt_results:
                results[vid] = attempt_results[vid]
                continue
            entry = next(
                (item for item in parsed.get("verbs", []) if item.get("id") == vid),
                None,
            )
            if isinstance(entry, dict):
                merged = merge_verb_examples_from_response(
                    forms,
                    entry.get("examples"),
                    merged,
                    examples_per=examples_per,
                )
                partial[vid] = merged
                if verb_examples_complete(forms, merged):
                    results[vid] = merged

        _log_verb_rejections(parsed, pending, results, examples_per=examples_per, progress=log)
        for verb, forms in pending:
            if verb["id"] not in results:
                missing = missing_verb_cells(forms, partial.get(verb["id"], {}))
                if missing and attempt == max_attempts - 1:
                    need = missing[0]
                    log(
                        f"  rejected {verb['hangul']}: still missing {need[0]}/{need[1]} "
                        f"(need form {need[2]!r})"
                    )

    logger.debug(
        "Verb batch generation result batch_size=%s matched_verbs=%s verb_hangul=%s",
        len(batch),
        len(results),
        [verb["hangul"] for verb, _ in batch],
    )
    return results


def generate_noun_batch(
    nouns: list[dict[str, Any]],
    *,
    level: LanguageLevel,
    vocabulary_context: str,
    llm: LlmClient,
    prompts: PromptProvider,
    temperature: float,
    verbose: bool,
    examples_per: int = 2,
    progress: ProgressFn | None = None,
) -> dict[str, list[dict[str, str]]]:
    payload = {"entries": [{"id": noun["id"], "hangul": noun["hangul"], "english": noun["english"]} for noun in nouns]}
    parsed = _chat_json(
        system=prompts.noun_examples_system_prompt(level, vocabulary_context, examples_per=examples_per),
        user=(f"Generate {examples_per} example sentence(s) per noun:\n" + json.dumps(payload, ensure_ascii=False, indent=2)),
        llm=llm,
        temperature=temperature,
        verbose=verbose,
        progress=progress,
    )
    if parsed is None:
        return {}

    results: dict[str, list[dict[str, str]]] = {}
    entries = parsed.get("entries", parsed if isinstance(parsed, list) else [])
    if not isinstance(entries, list):
        return results

    expected = {noun["id"]: noun for noun in nouns}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id")
        if entry_id not in expected:
            continue
        noun = expected[entry_id]
        raw_examples = entry.get("examples", [])
        if not isinstance(raw_examples, list):
            continue
        cleaned = validate_noun_examples(raw_examples, noun["hangul"], examples_per=examples_per)
        if cleaned:
            results[entry_id] = cleaned
    return results
