# SPDX-License-Identifier: BSD-3-Clause
"""Generate vocabulary example sentences via an injected LLM (no CLI).

Form checks go through :func:`soju.languages.get_language`; English quality through
:func:`soju.base.get_base_language`.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

from soju.base import get_base_language
from soju.core.logging import get_logger
from soju.core.models import EXAMPLE_TENSES as TENSES
from soju.core.models import EXAMPLE_VARIANTS as VARIANTS
from soju.languages import get_language
from soju.languages.contracts import PromptProvider
from soju.levels import LanguageLevel, get_language_level
from soju.llm.base import LlmClient, LlmError
from soju.prompts.context import build_vocabulary_context
from soju.registry.examples import (
    load_examples_store,
    noun_entry_needs_fill,
    save_examples_store,
    verb_entry_needs_fill,
    verb_examples_complete,
)
from soju.registry.verbs import load_verb_forms, load_verb_forms_cache
from soju.registry.vocabulary import vocabulary_by_type

logger = get_logger(__name__)

JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_json_content(content: str) -> Any:
    stripped = JSON_FENCE.sub("", content.strip())
    return json.loads(stripped)


def clean_example(example: dict[str, Any]) -> dict[str, str] | None:
    if not isinstance(example, dict):
        return None
    if "hangul" not in example or "english" not in example:
        return None
    base = get_base_language()
    return {
        "hangul": get_language().normalize(str(example["hangul"])),
        "english": base.scrub_example_gloss(base.normalize(str(example["english"]))),
    }


def diagnose_verb_examples(
    forms: dict[str, dict[str, str]],
    examples: Any,
    *,
    examples_per: int = 1,
) -> list[str]:
    if not isinstance(examples, dict):
        return ["model returned invalid examples object"]
    reasons: list[str] = []
    for tense in TENSES:
        tense_data = examples.get(tense)
        if not isinstance(tense_data, dict):
            reasons.append(f"{tense}: missing (check JSON nesting — past/future must be siblings)")
            continue
        for variant in VARIANTS:
            form = forms.get(tense, {}).get(variant)
            if not form:
                continue
            raw_list = tense_data.get(variant)
            if not isinstance(raw_list, list) or not raw_list:
                reasons.append(f"{tense}/{variant}: no examples")
                continue
            accepted = False
            for raw in raw_list[:examples_per]:
                example = clean_example(raw)
                if not example:
                    reasons.append(f"{tense}/{variant}: invalid example object")
                    continue
                if not get_language().form_in_sentence(form, example["hangul"]):
                    reasons.append(f"{tense}/{variant}: need form {form!r} inside {example['hangul']!r}")
                    continue
                if not get_base_language().is_acceptable_gloss(example["english"], tense=tense):
                    reasons.append(f"{tense}/{variant}: unacceptable English ({example['english']!r})")
                    continue
                accepted = True
                break
            if not accepted and not any(r.startswith(f"{tense}/{variant}:") for r in reasons):
                reasons.append(f"{tense}/{variant}: no valid example")
    return reasons


def clean_examples_store(examples_store: dict[str, Any]) -> int:
    changed = 0
    for entry in examples_store.values():
        if not isinstance(entry, dict):
            continue
        if "default" in entry and isinstance(entry["default"], list):
            for example in entry["default"]:
                if not isinstance(example, dict) or "english" not in example:
                    continue
                cleaned = get_base_language().scrub_example_gloss(str(example["english"]))
                if cleaned != example["english"]:
                    example["english"] = cleaned
                    changed += 1
            continue
        for tense in TENSES:
            tense_map = entry.get(tense)
            if not isinstance(tense_map, dict):
                continue
            for variant in VARIANTS:
                examples = tense_map.get(variant)
                if not isinstance(examples, list):
                    continue
                for example in examples:
                    if not isinstance(example, dict) or "english" not in example:
                        continue
                    cleaned = get_base_language().scrub_example_gloss(str(example["english"]))
                    if cleaned != example["english"]:
                        example["english"] = cleaned
                        changed += 1
    return changed


def validate_variant_examples(
    form: str,
    raw_list: Any,
    *,
    tense: str | None = None,
    examples_per: int = 1,
) -> list[dict[str, str]] | None:
    if not isinstance(raw_list, list) or not raw_list:
        return None
    variant_examples: list[dict[str, str]] = []
    for raw in raw_list[:examples_per]:
        example = clean_example(raw)
        if not example or not get_language().form_in_sentence(form, example["hangul"]):
            continue
        if not get_base_language().is_acceptable_gloss(example["english"], tense=tense):
            continue
        variant_examples.append(example)
    return variant_examples or None


def missing_verb_cells(
    forms: dict[str, dict[str, str]],
    examples: dict[str, dict[str, list[dict[str, str]]]],
) -> list[tuple[str, str, str]]:
    missing: list[tuple[str, str, str]] = []
    for tense in TENSES:
        for variant in VARIANTS:
            form = forms.get(tense, {}).get(variant)
            if form and not examples.get(tense, {}).get(variant):
                missing.append((tense, variant, form))
    return missing


def merge_verb_examples_from_response(
    forms: dict[str, dict[str, str]],
    examples: Any,
    existing: dict[str, dict[str, list[dict[str, str]]]],
    *,
    examples_per: int,
) -> dict[str, dict[str, list[dict[str, str]]]]:
    merged = {tense: dict(variants) for tense, variants in existing.items()}
    if not isinstance(examples, dict):
        return merged
    for tense in TENSES:
        tense_data = examples.get(tense)
        if not isinstance(tense_data, dict):
            continue
        tense_out = merged.setdefault(tense, {})
        for variant in VARIANTS:
            if variant in tense_out:
                continue
            form = forms.get(tense, {}).get(variant)
            if not form:
                continue
            validated = validate_variant_examples(
                form,
                tense_data.get(variant),
                tense=tense,
                examples_per=examples_per,
            )
            if validated:
                tense_out[variant] = validated
    return merged


def validate_tense_examples(
    forms: dict[str, str],
    examples: Any,
    *,
    tense: str | None = None,
    examples_per: int = 1,
) -> dict[str, list[dict[str, str]]] | None:
    if not isinstance(examples, dict):
        return None
    cleaned: dict[str, list[dict[str, str]]] = {}
    for variant in VARIANTS:
        form = forms.get(variant)
        if not form:
            continue
        raw_list = examples.get(variant)
        if not isinstance(raw_list, list) or not raw_list:
            return None
        variant_examples: list[dict[str, str]] = []
        for raw in raw_list[:examples_per]:
            example = clean_example(raw)
            if not example or not get_language().form_in_sentence(form, example["hangul"]):
                continue
            if not get_base_language().is_acceptable_gloss(example["english"], tense=tense):
                continue
            variant_examples.append(example)
        if not variant_examples:
            return None
        cleaned[variant] = variant_examples
    expected = [v for v in VARIANTS if forms.get(v)]
    return cleaned if len(cleaned) == len(expected) else None


def validate_verb_examples(
    forms: dict[str, dict[str, str]],
    examples: Any,
    *,
    examples_per: int = 1,
) -> dict[str, dict[str, list[dict[str, str]]]] | None:
    if not isinstance(examples, dict):
        return None
    result: dict[str, dict[str, list[dict[str, str]]]] = {}
    for tense in TENSES:
        tense_examples = validate_tense_examples(
            forms.get(tense, {}),
            examples.get(tense),
            tense=tense,
            examples_per=examples_per,
        )
        if not tense_examples:
            return None
        result[tense] = tense_examples
    return result


def validate_noun_examples(examples: list[Any], hangul: str, *, examples_per: int = 2) -> list[dict[str, str]] | None:
    cleaned: list[dict[str, str]] = []
    for raw in examples:
        example = clean_example(raw)
        if example and get_base_language().is_acceptable_gloss(example["english"]):
            cleaned.append(example)
    if not cleaned:
        return None
    if not any(hangul in ex["hangul"] for ex in cleaned):
        return None
    return cleaned[:examples_per]


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
        sample = forms.get("past", {}).get("casual_polite") or next(forms[t][v] for t in TENSES for v in VARIANTS if forms.get(t, {}).get(v))
        lines.append(f'- {verb["hangul"]}: example past/casual_polite hangul = "어제 친구하고 {sample}." — do NOT change {sample.rsplit(" ", 1)[0]!r} to another place.')
        missing = missing_verb_cells(forms, (partial or {}).get(verb["id"], {}))
        if missing:
            need = ", ".join(f"{t}/{v}={form!r}" for t, v, form in missing[:6])
            lines.append(f"- {verb['hangul']}: still required cells: {need}")
    payload = {"verbs": [_verb_payload_item(verb, forms) for verb, forms in batch]}
    lines.append(json.dumps(payload, ensure_ascii=False, indent=2))
    return "\n".join(lines)


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


def _log_verb_rejections(
    parsed: Any,
    batch: list[tuple[dict[str, Any], dict[str, dict[str, str]]]],
    matched: dict[str, Any],
    *,
    examples_per: int,
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
            print(
                f"  rejected {verb['hangul']}: missing from model response",
                file=sys.stderr,
            )
            continue
        reasons = diagnose_verb_examples(forms, entry.get("examples"), examples_per=examples_per)
        if reasons:
            print(f"  rejected {verb['hangul']}: {reasons[0]}", file=sys.stderr)


def _chat_json(
    *,
    system: str,
    user: str,
    llm: LlmClient,
    temperature: float,
    verbose: bool,
) -> Any | None:
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
        print(content, file=sys.stderr)
    try:
        parsed = parse_json_content(content)
    except json.JSONDecodeError:
        logger.debug("JSON parse failed content_head=%r", content[:300])
        print("  LLM returned unparseable JSON.", file=sys.stderr)
        if verbose:
            print(content, file=sys.stderr)
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
) -> dict[str, dict[str, dict[str, list[dict[str, str]]]]]:
    results: dict[str, dict[str, dict[str, list[dict[str, str]]]]] = {}
    partial: dict[str, dict[str, dict[str, list[dict[str, str]]]]] = {verb["id"]: {} for verb, _ in batch}
    pending = list(batch)

    for attempt in range(max(1, max_attempts)):
        pending = [(verb, forms) for verb, forms in batch if verb["id"] not in results]
        if not pending:
            break
        if attempt > 0:
            labels = ", ".join(verb["hangul"] for verb, _ in pending)
            print(f"  retry {attempt + 1}/{max_attempts}: {labels}", file=sys.stderr)

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

        _log_verb_rejections(parsed, pending, results, examples_per=examples_per)
        for verb, forms in pending:
            if verb["id"] not in results:
                missing = missing_verb_cells(forms, partial.get(verb["id"], {}))
                if missing and attempt == max_attempts - 1:
                    need = missing[0]
                    print(
                        f"  rejected {verb['hangul']}: still missing {need[0]}/{need[1]} (need form {need[2]!r})",
                        file=sys.stderr,
                    )

    logger.debug(
        "Verb batch generation result batch_size=%s matched_verbs=%s verb_hangul=%s",
        len(batch),
        len(results),
        [verb["hangul"] for verb, _ in batch],
    )
    return results


def filter_verbs_for_fill_mode(
    prepared: list[tuple[dict[str, Any], dict[str, dict[str, str]]]],
    examples_store: dict[str, Any],
    *,
    fill_mode: str,
) -> list[tuple[dict[str, Any], dict[str, dict[str, str]]]]:
    if fill_mode == "refresh-all":
        return prepared
    return [(verb, forms) for verb, forms in prepared if verb_entry_needs_fill(forms, examples_store.get(verb["id"]))]


def filter_nouns_for_fill_mode(
    noun_entries: list[dict[str, Any]],
    examples_store: dict[str, Any],
    *,
    fill_mode: str,
) -> list[dict[str, Any]]:
    if fill_mode == "refresh-all":
        return noun_entries
    return [noun for noun in noun_entries if noun_entry_needs_fill(examples_store.get(noun["id"]))]


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
) -> dict[str, list[dict[str, str]]]:
    payload = {"entries": [{"id": noun["id"], "hangul": noun["hangul"], "english": noun["english"]} for noun in nouns]}
    parsed = _chat_json(
        system=prompts.noun_examples_system_prompt(level, vocabulary_context, examples_per=examples_per),
        user=(f"Generate {examples_per} example sentence(s) per noun:\n" + json.dumps(payload, ensure_ascii=False, indent=2)),
        llm=llm,
        temperature=temperature,
        verbose=verbose,
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


def _fill_examples_local(
    *,
    level_id: str,
    verbs: bool,
    nouns: bool,
    examples_per: int,
    fill_mode: str,
    root=None,
) -> tuple[dict[str, Any], int]:
    """Fill examples using the active language plugin's deterministic generators."""
    from soju.levels import vocabulary_for_level

    lang = get_language()
    examples_store = load_examples_store(root)
    updated = 0

    if verbs:
        verb_entries = [e for e in vocabulary_for_level(level_id, root) if e.get("type") == "verb"]
        if not verb_entries:
            verb_entries = vocabulary_by_type("verb", root)
        forms_cache = load_verb_forms_cache(root)
        for verb in verb_entries:
            forms = load_verb_forms(verb["id"], root, cache=forms_cache)
            if not all(forms.get(t, {}).get(v) for t in TENSES for v in VARIANTS):
                continue
            if fill_mode == "fill-empty" and not verb_entry_needs_fill(forms, examples_store.get(verb["id"])):
                continue
            examples_store[verb["id"]] = lang.examples_for_verb(
                verb["hangul"],
                verb["english"],
                forms,
                level_id=level_id,
            )
            updated += 1

    if nouns:
        noun_entries = [e for e in vocabulary_for_level(level_id, root) if e.get("type") == "noun"]
        if not noun_entries:
            noun_entries = vocabulary_by_type("noun", root)
        for noun in noun_entries:
            if fill_mode == "fill-empty" and not noun_entry_needs_fill(examples_store.get(noun["id"])):
                continue
            examples_store[noun["id"]] = {
                "default": lang.examples_for_noun(
                    noun["hangul"],
                    noun["english"],
                    level_id=level_id,
                    examples_per=examples_per,
                )
            }
            updated += 1

    return examples_store, updated


def fill_examples(
    *,
    llm: LlmClient | None,
    prompts: PromptProvider | None = None,
    temperature: float,
    verb_batch_size: int,
    noun_batch_size: int,
    verbs: bool,
    nouns: bool,
    limit: int | None,
    clean_only: bool,
    verbose: bool,
    level_id: str | None,
    local: bool = False,
    examples_per: int = 1,
    max_attempts: int = 3,
    fill_mode: str = "fill-empty",
    root=None,
) -> tuple[dict[str, Any], list[str], int]:
    examples_store = load_examples_store(root)
    warnings: list[str] = []
    updated = 0

    cleaned = clean_examples_store(examples_store)
    if cleaned:
        print(
            f"Stripped register notes from {cleaned} example translation(s).",
            file=sys.stderr,
        )

    if clean_only:
        return examples_store, warnings, cleaned

    if local:
        level = get_language_level(level_id, root)
        print(
            f"Language level: {level.label} ({level.id}) [local templates]",
            file=sys.stderr,
        )
        print(f"Fill mode: {fill_mode}", file=sys.stderr)
        examples_store, updated = _fill_examples_local(
            level_id=level.id,
            verbs=verbs,
            nouns=nouns,
            examples_per=examples_per,
            fill_mode=fill_mode,
            root=root,
        )
        if limit is not None:
            warnings.append(f"--limit is ignored with --local (generated {updated} entries).")
        return examples_store, warnings, updated

    if llm is None:
        raise ValueError("llm is required unless local=True or clean_only=True")
    prompt_provider = prompts if prompts is not None else get_language()

    level = get_language_level(level_id, root)
    vocabulary_context = build_vocabulary_context(root, compact=True, level=level)
    print(f"Language level: {level.label} ({level.id})", file=sys.stderr)
    print(f"Examples per variant: {examples_per}", file=sys.stderr)
    print(f"Fill mode: {fill_mode}", file=sys.stderr)
    if verb_batch_size >= 10 and verbs:
        print(
            f"Note: verb batch size {verb_batch_size} can take several minutes per batch before the next status line appears.",
            file=sys.stderr,
        )

    if verbs:
        verb_entries = vocabulary_by_type("verb", root)
        if limit is not None:
            verb_entries = verb_entries[:limit]

        forms_cache = load_verb_forms_cache(root)
        prepared: list[tuple[dict[str, Any], dict[str, dict[str, str]]]] = []
        for verb in verb_entries:
            forms = load_verb_forms(verb["id"], root, cache=forms_cache)
            if not all(forms.get(tense, {}).get(variant) for tense in TENSES for variant in VARIANTS):
                warnings.append(f"Skipped {verb['hangul']}: missing conjugated forms.")
                continue
            prepared.append((verb, forms))

        prepared = filter_verbs_for_fill_mode(prepared, examples_store, fill_mode=fill_mode)
        if fill_mode == "fill-empty" and not prepared and verb_entries:
            print("All verb examples are already complete.", file=sys.stderr)

        batch_size = max(1, verb_batch_size)
        for start in range(0, len(prepared), batch_size):
            batch = prepared[start : start + batch_size]
            end = start + len(batch)
            labels = ", ".join(verb["hangul"] for verb, _ in batch)
            print(f"verbs {start + 1}-{end}/{len(prepared)}: {labels}", file=sys.stderr)

            generated = generate_verb_batch(
                batch,
                level=level,
                vocabulary_context=vocabulary_context,
                llm=llm,
                prompts=prompt_provider,
                temperature=temperature,
                verbose=verbose,
                examples_per=examples_per,
                max_attempts=max_attempts,
            )

            for verb, forms in batch:
                examples = generated.get(verb["id"])
                if not examples:
                    warnings.append(f"Failed to generate verb examples: {verb['hangul']}")
                    continue
                examples_store[verb["id"]] = examples
                updated += 1

            save_examples_store(examples_store, root)

    if nouns:
        noun_entries = vocabulary_by_type("noun", root)
        if limit is not None and not verbs:
            noun_entries = noun_entries[:limit]
        elif limit is not None:
            noun_entries = noun_entries[: max(0, limit - updated)]

        noun_entries = filter_nouns_for_fill_mode(noun_entries, examples_store, fill_mode=fill_mode)
        if fill_mode == "fill-empty" and not noun_entries and vocabulary_by_type("noun", root):
            print("All noun examples are already complete.", file=sys.stderr)

        batch_size = max(1, noun_batch_size)
        for start in range(0, len(noun_entries), batch_size):
            batch = noun_entries[start : start + batch_size]
            print(
                f"nouns {start + 1}-{start + len(batch)}/{len(noun_entries)}",
                file=sys.stderr,
            )
            generated = generate_noun_batch(
                batch,
                level=level,
                vocabulary_context=vocabulary_context,
                llm=llm,
                prompts=prompt_provider,
                temperature=temperature,
                verbose=verbose,
                examples_per=examples_per,
            )
            for noun in batch:
                examples = generated.get(noun["id"])
                if not examples:
                    warnings.append(f"Failed to generate noun examples: {noun['hangul']}")
                    continue
                examples_store[noun["id"]] = {"default": examples}
                updated += 1

            save_examples_store(examples_store, root)

    return examples_store, warnings, updated
