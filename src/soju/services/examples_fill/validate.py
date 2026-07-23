# SPDX-License-Identifier: BSD-3-Clause
"""Validate and filter vocabulary example payloads."""

from __future__ import annotations

from typing import Any

from soju.base import get_base_language
from soju.core.models import EXAMPLE_TENSES as TENSES
from soju.core.models import EXAMPLE_VARIANTS as VARIANTS
from soju.languages import get_language
from soju.registry.examples import noun_entry_needs_fill, verb_entry_needs_fill


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
