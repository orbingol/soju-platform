# SPDX-License-Identifier: BSD-3-Clause
"""Generate vocabulary example sentences via Ollama."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

from soju.debug_log import debug_log
from soju import db, ollama_client
from soju.korean_levels import KoreanLevel, get_korean_level, list_level_ids
from soju.ollama_client import OllamaError
from soju.vocabulary_context import build_vocabulary_context

TENSES = ("present", "past", "future")
VARIANTS = ("casual_polite", "formal_polite")
PAREN_ENGLISH = re.compile(r"\s*\([^)]*\)")
BROKEN_PAST_ENGLISH = re.compile(
    r"\b(?:readed|eated|goed|knowed|teached|meeted|giveed|swimed|arriveed|loveed|"
    r"saied|comeed|shoped|drink watered|buied|danceed|thinked|not knowed|movieed|"
    r"tennised|guitared|drumsed|homeworked|work outed|interneted|moneied|gameed|"
    r"newspapered|laundryed|restauranted|visaed|pooled|houseed|begined|mountained|"
    r"relocateed|schooled|faceed|phoneed|sended|tidy uped)\b",
    re.IGNORECASE,
)
JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def verb_batch_json_schema(examples_per: int) -> str:
    slots = ", ".join(['{"hangul": "...", "english": "..."}'] * examples_per)
    return f"""{{
  "verbs": [
    {{
      "id": "<uuid from input>",
      "examples": {{
        "present": {{
          "casual_polite": [{slots}],
          "formal_polite": [{slots}]
        }},
        "past": {{
          "casual_polite": [{slots}],
          "formal_polite": [{slots}]
        }},
        "future": {{
          "casual_polite": [{slots}],
          "formal_polite": [{slots}]
        }}
      }}
    }}
  ]
}}"""


def parse_json_content(content: str) -> Any:
    stripped = JSON_FENCE.sub("", content.strip())
    return json.loads(stripped)


def strip_example_english(text: str) -> str:
    cleaned = PAREN_ENGLISH.sub("", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def clean_example(example: dict[str, Any]) -> dict[str, str] | None:
    if not isinstance(example, dict):
        return None
    if "hangul" not in example or "english" not in example:
        return None
    return {
        "hangul": db.normalize_hangul(str(example["hangul"])),
        "english": strip_example_english(db.normalize_english(str(example["english"]))),
    }


_HADA_CONJUGATIONS = (
    "해요",
    "합니다",
    "했어요",
    "했습니다",
    "할 거예요",
    "하겠습니다",
)

_SUBJECT_PREFIXES = (
    "저는",
    "저희는",
    "우리는",
    "제가",
    "친구가",
    "선생님이",
    "학생이",
    "동생이",
    "엄마가",
    "아버지가",
    "할머니가",
    "할아버지가",
    "그가",
    "그녀가",
)

# Same verb, different natural wording (canonical stem -> alternates).
_VERB_STEM_SYNONYMS: dict[str, tuple[str, ...]] = {
    "씻": ("샤워", "목욕"),
}


def _compact_hangul(text: str) -> str:
    return text.replace(" ", "")


def _strip_leading_subjects(hangul: str) -> str:
    text = hangul.strip()
    while True:
        stripped = False
        for prefix in _SUBJECT_PREFIXES:
            if text.startswith(prefix):
                text = text[len(prefix) :].lstrip()
                stripped = True
                break
        if not stripped:
            break
    return text


def _hada_alternate_forms(form: str) -> set[str]:
    """Accept natural 하다 splits and object reordering when conjugation matches."""
    alts = {form}
    obj_match = re.match(
        rf"^(.+)(를|을) ({'|'.join(_HADA_CONJUGATIONS)})$",
        form,
    )
    if obj_match:
        obj, _, ending = obj_match.groups()
        stem = obj
        alts.add(f"{stem}{ending}")
        alts.add(f"{obj} {ending}")
        return alts
    compact_match = re.match(
        rf"^(.+?)({'|'.join(_HADA_CONJUGATIONS)})$",
        form,
    )
    if compact_match:
        stem, ending = compact_match.groups()
        if stem.endswith(("를", "을")):
            return alts
        for particle in ("를", "을"):
            alts.add(f"{stem}{particle} {ending}")
    return alts


def _synonym_alternate_forms(form: str) -> set[str]:
    alts: set[str] = set()
    for canonical, synonyms in _VERB_STEM_SYNONYMS.items():
        if canonical not in form:
            continue
        for synonym in synonyms:
            alts.add(form.replace(canonical, synonym, 1))
            obj_match = re.match(
                rf"^{canonical}(어요|습니다|었어요|었습니다|을 거예요|겠습니다)$",
                form,
            )
            if obj_match and synonym == "샤워":
                ending = obj_match.group(1)
                if ending.startswith("었"):
                    alts.add(f"샤워했{ending[1:]}")
                    alts.add(f"샤워를 했{ending[1:]}")
                elif ending == "어요":
                    alts.add("샤워해요")
                    alts.add("샤워를 해요")
                elif ending == "습니다":
                    alts.add("샤워합니다")
                    alts.add("샤워를 합니다")
                elif ending.startswith("을 "):
                    alts.add(f"샤워{ending}")
                    alts.add(f"샤워를 {ending}")
                elif ending == "겠습니다":
                    alts.add("샤워하겠습니다")
                    alts.add("샤워를 하겠습니다")
    return alts


def _alternate_form_compacts(form: str) -> set[str]:
    compacts = {_compact_hangul(form)}
    for alt in _hada_alternate_forms(form) | _synonym_alternate_forms(form):
        compacts.add(_compact_hangul(alt))
    return compacts


def form_in_sentence(form: str, hangul: str) -> bool:
    form_compacts = _alternate_form_compacts(form)
    for candidate in (hangul, _strip_leading_subjects(hangul)):
        hangul_compact = _compact_hangul(candidate)
        if any(alt in hangul_compact for alt in form_compacts):
            return True
    return False


def embedded_form_hint(forms: dict[str, dict[str, str]]) -> str | None:
    """Hint when conjugated forms embed a destination/object prefix the model must keep."""
    all_forms = [forms[tense][variant] for tense in TENSES for variant in VARIANTS if forms.get(tense, {}).get(variant)]
    if not all_forms or " " not in all_forms[0]:
        return None
    prefix = all_forms[0].rsplit(" ", 1)[0]
    if not all(form.startswith(f"{prefix} ") for form in all_forms):
        return None
    sample = all_forms[0]
    return (
        f"Every hangul example MUST contain the exact form substring for that cell "
        f"(e.g. {sample!r}). The prefix {prefix!r} is fixed in ALL variants including "
        f"formal_polite — add context around it, but do NOT replace {prefix!r} with 회사에, "
        f"집에, 공원에, or any other place."
    )


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
                if not form_in_sentence(form, example["hangul"]):
                    reasons.append(f"{tense}/{variant}: need form {form!r} inside {example['hangul']!r}")
                    continue
                if is_bad_english(example["english"], tense):
                    reasons.append(f"{tense}/{variant}: bad English ({example['english']!r})")
                    continue
                if is_bare_english(example["english"]):
                    reasons.append(f"{tense}/{variant}: too bare ({example['english']!r})")
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
                cleaned = strip_example_english(str(example["english"]))
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
                    cleaned = strip_example_english(str(example["english"]))
                    if cleaned != example["english"]:
                        example["english"] = cleaned
                        changed += 1
    return changed


def load_verb_forms_cache(root=None) -> dict[str, dict]:
    return {tense: db.load_verb_forms_file(tense, root) for tense in TENSES}


def load_verb_forms(
    verb_id: str,
    root=None,
    *,
    cache: dict[str, dict] | None = None,
) -> dict[str, dict[str, str]]:
    forms_by_tense = cache if cache is not None else load_verb_forms_cache(root)
    forms: dict[str, dict[str, str]] = {}
    for tense in TENSES:
        tense_forms = forms_by_tense.get(tense, {}).get(verb_id, {})
        if isinstance(tense_forms, dict):
            forms[tense] = {variant: str(tense_forms[variant]) for variant in VARIANTS if variant in tense_forms}
    return forms


def is_bad_english(english: str, tense: str | None = None) -> bool:
    if tense == "past" and BROKEN_PAST_ENGLISH.search(english):
        return True
    if PAREN_ENGLISH.search(english):
        return True
    return False


def is_bare_english(english: str) -> bool:
    """Reject time-only glosses like 'I talked last week.' with no place/object/context."""
    s = english.strip().rstrip(".")
    if re.match(
        r"^I (?:will )?\w+ (yesterday|today|tomorrow|now|last week|next week)$",
        s,
        re.IGNORECASE,
    ):
        return True
    return bool(re.match(r"^I (?:will )?\w+$", s, re.IGNORECASE))


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
        if not example or not form_in_sentence(form, example["hangul"]):
            continue
        if is_bad_english(example["english"], tense) or is_bare_english(example["english"]):
            continue
        variant_examples.append(example)
    return variant_examples or None


def verb_examples_complete(
    forms: dict[str, dict[str, str]],
    examples: dict[str, dict[str, list[dict[str, str]]]],
) -> bool:
    return db.verb_examples_complete(forms, examples)


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
            if not example or not form_in_sentence(form, example["hangul"]):
                continue
            if is_bad_english(example["english"], tense) or is_bare_english(example["english"]):
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
        if example and not is_bare_english(example["english"]):
            cleaned.append(example)
    if not cleaned:
        return None
    if not any(hangul in ex["hangul"] for ex in cleaned):
        return None
    return cleaned[:examples_per]


def verb_batch_system_prompt(level: KoreanLevel, vocabulary_context: str, *, examples_per: int) -> str:
    return f"""You write Korean example sentences for a {level.label} learner app.

Level guidance:
{level.guidance}

{vocabulary_context}

You will receive several verbs in one request. For EACH verb, write {examples_per} example sentence(s) per tense and variant (present/past/future × casual_polite/formal_polite).

Quality rules (very important):
- Each hangul sentence MUST contain the EXACT conjugated form string from `forms` for that tense/variant, as one contiguous substring. Add context before or after (time, friend, reason), but never alter embedded pieces of the form (e.g. keep 학교에 if the form is 학교에 가요; keep 책을 if the form is 책을 읽어요).
- If a verb includes `form_rule`, follow it strictly.
- English must describe the full situation, not just the verb + time.
- Write {examples_per} DISTINCT examples per cell when possible (different partners or time words, not different destinations when the form fixes one).

GOOD example when form is 학교에 갔어요:
{{"hangul": "어제 친구하고 학교에 갔어요.", "english": "I went to school with a friend yesterday."}}

BAD when form is 학교에 갔어요 (swapped destination):
{{"hangul": "어제 공원에 갔어요.", "english": "I went to the park yesterday."}}

Other rules:
- Return one object per input verb, using the exact id from the input.
- English must NOT include parenthetical register notes like (formal) or (casual / common).
- Past tense English: correct irregulars (went, ate, read, talked — never goed/eated/readed).
- Future tense English: "will" + verb.
- JSON shape: `present`, `past`, and `future` are sibling keys under `examples` (do not nest future inside past).
- Return ONLY valid JSON matching this schema (no markdown fences, no prose):

{verb_batch_json_schema(examples_per)}"""


def noun_batch_system_prompt(level: KoreanLevel, vocabulary_context: str, *, examples_per: int) -> str:
    return f"""You write Korean example sentences for a {level.label} learner app.

Level guidance:
{level.guidance}

{vocabulary_context}

For each noun, write {examples_per} natural example sentence(s) using the word in a real situation with other vocabulary from the list above.
Each example should add context (where, with whom, why) — not just "This is X" or "I have X" repeated with different time words.
Return one object per input noun using the exact id from the input.
English must be natural and must NOT include parenthetical register notes.

Return ONLY valid JSON (no markdown fences, no prose):
{{"entries": [{{"id": "<uuid>", "examples": [{{"hangul": "...", "english": "..."}}]}}]}}"""


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
        if not embedded_form_hint(forms):
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
    hint = embedded_form_hint(forms)
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
    model: str,
    base_url: str,
    temperature: float,
    verbose: bool,
) -> Any | None:
    # #region agent log
    debug_log(
        "fill_examples.py:_chat_json:start",
        "fill_examples calling Ollama",
        {"model": model, "system_chars": len(system), "user_chars": len(user)},
        hypothesis_id="C",
    )
    # #endregion
    content = ollama_client.chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        model=model,
        base_url=base_url,
        json_mode=True,
        temperature=temperature,
        num_predict=8192,
    )
    if verbose:
        print(content, file=sys.stderr)
    try:
        parsed = parse_json_content(content)
    except json.JSONDecodeError:
        # #region agent log
        debug_log(
            "fill_examples.py:_chat_json:parse_fail",
            "JSON parse failed",
            {"model": model, "content_head": content[:300]},
            hypothesis_id="D",
        )
        # #endregion
        print("  Ollama returned unparseable JSON.", file=sys.stderr)
        if verbose:
            print(content, file=sys.stderr)
        return None
    # #region agent log
    debug_log(
        "fill_examples.py:_chat_json:parsed",
        "JSON parsed",
        {
            "model": model,
            "top_keys": list(parsed.keys()) if isinstance(parsed, dict) else type(parsed).__name__,
        },
        hypothesis_id="D",
    )
    # #endregion
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
    level: KoreanLevel,
    vocabulary_context: str,
    model: str,
    base_url: str,
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
            system=verb_batch_system_prompt(level, vocabulary_context, examples_per=examples_per),
            user=_verb_user_message(
                pending,
                examples_per=examples_per,
                partial=partial,
            ),
            model=model,
            base_url=base_url,
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

    # #region agent log
    debug_log(
        "fill_examples.py:generate_verb_batch",
        "Verb batch generation result",
        {
            "model": model,
            "batch_size": len(batch),
            "matched_verbs": len(results),
            "verb_hangul": [verb["hangul"] for verb, _ in batch],
        },
        hypothesis_id="D",
    )
    # #endregion
    return results


def generate_single_verb(
    verb: dict[str, Any],
    forms: dict[str, dict[str, str]],
    *,
    level: KoreanLevel,
    vocabulary_context: str,
    model: str,
    base_url: str,
    temperature: float,
    verbose: bool,
    examples_per: int = 1,
    max_attempts: int = 3,
) -> dict[str, dict[str, list[dict[str, str]]]] | None:
    result = generate_verb_batch(
        [(verb, forms)],
        level=level,
        vocabulary_context=vocabulary_context,
        model=model,
        base_url=base_url,
        temperature=temperature,
        verbose=verbose,
        examples_per=examples_per,
        max_attempts=max_attempts,
    )
    return result.get(verb["id"])


def filter_verbs_for_fill_mode(
    prepared: list[tuple[dict[str, Any], dict[str, dict[str, str]]]],
    examples_store: dict[str, Any],
    *,
    fill_mode: str,
) -> list[tuple[dict[str, Any], dict[str, dict[str, str]]]]:
    if fill_mode == "refresh-all":
        return prepared
    return [(verb, forms) for verb, forms in prepared if db.verb_entry_needs_fill(forms, examples_store.get(verb["id"]))]


def filter_nouns_for_fill_mode(
    noun_entries: list[dict[str, Any]],
    examples_store: dict[str, Any],
    *,
    fill_mode: str,
) -> list[dict[str, Any]]:
    if fill_mode == "refresh-all":
        return noun_entries
    return [noun for noun in noun_entries if db.noun_entry_needs_fill(examples_store.get(noun["id"]))]


def generate_noun_batch(
    nouns: list[dict[str, Any]],
    *,
    level: KoreanLevel,
    vocabulary_context: str,
    model: str,
    base_url: str,
    temperature: float,
    verbose: bool,
    examples_per: int = 2,
) -> dict[str, list[dict[str, str]]]:
    payload = {"entries": [{"id": noun["id"], "hangul": noun["hangul"], "english": noun["english"]} for noun in nouns]}
    parsed = _chat_json(
        system=noun_batch_system_prompt(level, vocabulary_context, examples_per=examples_per),
        user=(f"Generate {examples_per} example sentence(s) per noun:\n" + json.dumps(payload, ensure_ascii=False, indent=2)),
        model=model,
        base_url=base_url,
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


def fill_examples(
    *,
    model: str,
    base_url: str,
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
    examples_store = db.load_examples_store(root)
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
        from soju.local_examples import generate_all_local

        level = get_korean_level(level_id, root)
        print(
            f"Korean level: {level.label} ({level.id}) [local templates]",
            file=sys.stderr,
        )
        print(f"Fill mode: {fill_mode}", file=sys.stderr)
        examples_store, updated = generate_all_local(
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

    level = get_korean_level(level_id, root)
    vocabulary_context = build_vocabulary_context(root, compact=True, level=level)
    print(f"Korean level: {level.label} ({level.id})", file=sys.stderr)
    print(f"Examples per variant: {examples_per}", file=sys.stderr)
    print(f"Fill mode: {fill_mode}", file=sys.stderr)
    if verb_batch_size >= 10 and verbs:
        print(
            f"Note: verb batch size {verb_batch_size} with {model} can take several minutes per batch before the next status line appears.",
            file=sys.stderr,
        )

    if verbs:
        verb_entries = db.vocabulary_by_type("verb", root)
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
                model=model,
                base_url=base_url,
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

            db.save_examples_store(examples_store, root)

    if nouns:
        noun_entries = db.vocabulary_by_type("noun", root)
        if limit is not None and not verbs:
            noun_entries = noun_entries[:limit]
        elif limit is not None:
            noun_entries = noun_entries[: max(0, limit - updated)]

        noun_entries = filter_nouns_for_fill_mode(noun_entries, examples_store, fill_mode=fill_mode)
        if fill_mode == "fill-empty" and not noun_entries and db.vocabulary_by_type("noun", root):
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
                model=model,
                base_url=base_url,
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

            db.save_examples_store(examples_store, root)

    return examples_store, warnings, updated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate noun and verb example sentences via Ollama.")
    parser.add_argument("--model", default=ollama_client.DEFAULT_MODEL)
    parser.add_argument("--base-url", default=ollama_client.DEFAULT_BASE_URL)
    parser.add_argument("--temperature", type=float, default=0.4)
    parser.add_argument("--verb-batch-size", type=int, default=4, help="Verbs per Ollama request")
    parser.add_argument("--noun-batch-size", type=int, default=6, help="Nouns per Ollama request")
    parser.add_argument("--verbs-only", action="store_true")
    parser.add_argument("--nouns-only", action="store_true")
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Strip (formal)/(casual) notes from example English only",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Generate examples with local Korean 1A/1B templates (no Ollama)",
    )
    parser.add_argument(
        "--level",
        default=None,
        help=f"Korean course level (default: SOJU_KOREAN_LEVEL or 1A). Known: {', '.join(list_level_ids())}",
    )
    parser.add_argument(
        "--examples",
        type=int,
        default=1,
        metavar="N",
        help="Example sentences per verb tense/variant and per noun (default: 1)",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        metavar="N",
        help="Ollama attempts per verb batch before giving up (default: 3)",
    )
    parser.add_argument(
        "--mode",
        choices=("fill-empty", "refresh-all"),
        default="fill-empty",
        help="fill-empty: only entries missing examples (default); refresh-all: regenerate every entry",
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--limit", type=int, help="Process only the first N entries (testing)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if args.examples < 1:
        print("Error: --examples must be at least 1.", file=sys.stderr)
        return 1
    if args.max_attempts < 1:
        print("Error: --max-attempts must be at least 1.", file=sys.stderr)
        return 1

    verbs = not args.nouns_only and not args.clean_only
    nouns = not args.verbs_only and not args.clean_only
    if args.verbs_only:
        nouns = False

    if args.dry_run:
        level = get_korean_level(args.level)
        verb_count = len(db.vocabulary_by_type("verb"))
        noun_count = len(db.vocabulary_by_type("noun"))
        store = db.load_examples_store()
        if args.mode == "fill-empty" and verbs:
            forms_cache = load_verb_forms_cache()
            verb_prepared = []
            for verb in db.vocabulary_by_type("verb"):
                forms = load_verb_forms(verb["id"], cache=forms_cache)
                if all(forms.get(t, {}).get(v) for t in TENSES for v in VARIANTS):
                    verb_prepared.append((verb, forms))
            verb_count = len(
                filter_verbs_for_fill_mode(
                    verb_prepared,
                    store,
                    fill_mode=args.mode,
                )
            )
        if args.mode == "fill-empty" and nouns:
            noun_count = len(filter_nouns_for_fill_mode(db.vocabulary_by_type("noun"), store, fill_mode=args.mode))
        verb_batches = (verb_count + args.verb_batch_size - 1) // args.verb_batch_size if verb_count else 0
        noun_batches = (noun_count + args.noun_batch_size - 1) // args.noun_batch_size if noun_count else 0
        print(f"Korean level: {level.label} ({level.id})", file=sys.stderr)
        print(f"Fill mode: {args.mode}", file=sys.stderr)
        print(
            f"Would generate {args.examples} example(s) per variant for "
            f"{verb_count if verbs else 0} verbs "
            f"({verb_batches} batch(es) of up to {args.verb_batch_size}) and "
            f"{noun_count if nouns else 0} nouns "
            f"({noun_batches} batch(es) of up to {args.noun_batch_size}).",
            file=sys.stderr,
        )
        return 0

    if not args.clean_only and not args.local and not ollama_client.check_available(args.base_url):
        print(f"Error: Ollama is not reachable at {args.base_url}.", file=sys.stderr)
        return 1

    try:
        examples_store, warnings, updated = fill_examples(
            model=args.model,
            base_url=args.base_url,
            temperature=args.temperature,
            verb_batch_size=args.verb_batch_size,
            noun_batch_size=args.noun_batch_size,
            verbs=verbs,
            nouns=nouns,
            limit=args.limit,
            clean_only=args.clean_only,
            verbose=args.verbose,
            level_id=args.level,
            local=args.local,
            examples_per=args.examples,
            max_attempts=args.max_attempts,
            fill_mode=args.mode,
            root=None,
        )
    except (OllamaError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    db.save_examples_store(examples_store, root=None)

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if args.clean_only:
        print(
            f"Cleaned example translations ({updated} field(s) updated).",
            file=sys.stderr,
        )
    else:
        print(f"Generated examples for {updated} vocabulary entries.", file=sys.stderr)
    if warnings:
        print(f"{len(warnings)} warning(s).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
