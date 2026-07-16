# SPDX-License-Identifier: BSD-3-Clause
"""Translate a plain-text word list into soju-import JSON (no CLI).

Depends on an injected :class:`~soju.llm.base.LlmClient` and the active
language's :class:`~soju.languages.contracts.PromptProvider` for system prompts.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from soju.base import get_base_language
from soju.core.text import parse_import_line
from soju.languages import get_language
from soju.languages.contracts import PromptProvider
from soju.levels import LanguageLevel, get_language_level
from soju.llm.base import LlmClient, LlmError
from soju.prompts.context import build_vocabulary_context as _build_vocabulary_context
from soju.registry.vocabulary import vocabulary_by_sense
from soju.services.keys import sense_key

ARROW_LINE = re.compile(r"^(.+?)\s*->\s*(.+)$")
BULLET_PREFIX = re.compile(r"^[\*\-]\s*")
SECTION_HEADER = re.compile(r"^[A-Za-z][^:\uAC00-\uD7A3]*:$")


@dataclass
class WordHint:
    source_line: str
    entry: str
    hint_english: str | None = None
    hint_example: str | None = None


def strip_bullet(text: str) -> str:
    return BULLET_PREFIX.sub("", text.strip())


def parse_word_list_lines(lines: list[str]) -> list[WordHint]:
    hints: list[WordHint] = []
    lang = get_language()

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        text = strip_bullet(stripped)
        if not text:
            continue
        if SECTION_HEADER.match(text) and not lang.is_target_script(text):
            continue

        arrow = ARROW_LINE.match(text)
        if arrow:
            entry = arrow.group(1).strip()
            hint = arrow.group(2).strip()
            if lang.is_target_script(hint):
                hints.append(WordHint(raw, entry, hint_example=hint))
            else:
                hints.append(WordHint(raw, entry, hint_english=hint))
            continue

        parsed = parse_import_line(raw)
        if parsed:
            entry, example = parsed
            entry = strip_bullet(entry)
            if not lang.is_target_script(entry):
                if example and lang.is_target_script(example):
                    entry, example = example, entry
                else:
                    continue
            hint_english = None
            hint_example = None
            if example:
                if lang.is_target_script(example):
                    hint_example = example
                else:
                    hint_english = example
            hints.append(WordHint(raw, entry, hint_english, hint_example))
            continue

        if not lang.is_target_script(text):
            continue

        hints.append(WordHint(raw, text))

    return hints


def build_user_prompt(batch: list[WordHint]) -> str:
    items = []
    for hint in batch:
        payload: dict[str, str] = {"entry": hint.entry}
        if hint.hint_english:
            payload["english_hint"] = hint.hint_english
        if hint.hint_example:
            payload["example_hint"] = hint.hint_example
        items.append(payload)
    return "Translate these vocabulary items into records. Return one record per item, in the same order.\n" + json.dumps({"items": items}, ensure_ascii=False, indent=2)


def normalize_record(record: dict[str, Any]) -> dict[str, Any] | None:
    required = {"hangul", "romanization", "english"}
    if not required.issubset(record):
        return None

    lang = get_language()
    base = get_base_language()
    clean: dict[str, Any] = {
        "hangul": lang.normalize(str(record["hangul"])),
        "romanization": str(record["romanization"]).strip().lower(),
        "english": base.normalize_gloss(str(record["english"])),
        "type": str(record.get("type", "noun")).strip().lower() or "noun",
    }

    examples = record.get("examples") or []
    if isinstance(examples, list) and examples:
        parsed_examples = []
        for example in examples:
            if not isinstance(example, dict):
                continue
            if "hangul" not in example or "english" not in example:
                continue
            parsed_examples.append(
                {
                    "hangul": lang.normalize(str(example["hangul"])),
                    "english": base.normalize(str(example["english"])),
                }
            )
        if parsed_examples:
            clean["examples"] = parsed_examples

    return clean


def parse_batch_records(batch: list[WordHint], payload: Any) -> list[dict[str, Any]]:
    """Validate model JSON against the input batch. Raises ``ValueError`` on mismatch."""
    records = payload.get("records") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("Model JSON must contain a records array.")
    if len(records) != len(batch):
        raise ValueError(f"Expected {len(batch)} records, got {len(records)}.")

    cleaned: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"Record {index} is not an object.")
        normalized = normalize_record(record)
        if not normalized:
            raise ValueError(f"Record {index} is missing required fields (hangul, romanization, english).")
        cleaned.append(normalized)
    return cleaned


def translate_batch(
    batch: list[WordHint],
    *,
    level: LanguageLevel,
    vocabulary_context: str,
    llm: LlmClient,
    prompts: PromptProvider,
    temperature: float,
) -> list[dict[str, Any]]:
    """Call ``llm`` for one batch and parse the JSON records.

    Raises:
        LlmError: Provider/transport failures from ``llm``.
        ValueError: Invalid or mismatched model JSON.
    """
    content = llm.chat(
        [
            {
                "role": "system",
                "content": prompts.translation_system_prompt(level, vocabulary_context),
            },
            {"role": "user", "content": build_user_prompt(batch)},
        ],
        json_mode=True,
        temperature=temperature,
    )

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned invalid JSON: {exc}") from exc

    return parse_batch_records(batch, payload)


def translate_words(
    lines: list[str],
    *,
    llm: LlmClient,
    batch_size: int,
    temperature: float,
    skip_existing: bool,
    level_id: str | None,
    prompts: PromptProvider | None = None,
    root=None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Translate word-list lines into soju-import records.

    Args:
        lines: Raw input lines from a plain-text word list.
        llm: Injected chat client (e.g. :class:`~soju.llm.ollama.OllamaClient`).
        batch_size: Items per LLM request.
        temperature: Sampling temperature.
        skip_existing: Omit senses already in the registry.
        level_id: Course level id (or ``None`` for env/default).
        prompts: Prompt provider; defaults to the active language plugin.
        root: Optional data root override.

    Returns:
        ``(records, warnings)``.

    Raises:
        LlmError: On LLM provider failures.
        ValueError: On batch parse failures.
    """
    hints = parse_word_list_lines(lines)
    if not hints:
        return [], ["No translatable lines found in input."]

    prompt_provider = prompts if prompts is not None else get_language()
    level = get_language_level(level_id, root)
    vocabulary_context = _build_vocabulary_context(root, compact=False, level=level)
    existing = vocabulary_by_sense(root, sense_key=sense_key) if skip_existing else {}
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen: set[tuple[str, str]] = set()

    for start in range(0, len(hints), batch_size):
        batch = hints[start : start + batch_size]
        batch_index = start // batch_size + 1
        try:
            batch_records = translate_batch(
                batch,
                level=level,
                vocabulary_context=vocabulary_context,
                llm=llm,
                prompts=prompt_provider,
                temperature=temperature,
            )
        except LlmError:
            raise
        except ValueError as exc:
            raise ValueError(f"Batch {batch_index}: {exc}") from exc

        for record in batch_records:
            key = sense_key(record["hangul"], record["english"])
            if skip_existing and key in existing:
                warnings.append(f"Skipped existing registry entry: {record['hangul']} ({record['english']})")
                continue
            if key in seen:
                warnings.append(f"Skipped duplicate in output: {record['hangul']} ({record['english']})")
                continue
            seen.add(key)
            records.append(record)

    return records, warnings
