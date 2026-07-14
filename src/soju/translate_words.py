# SPDX-License-Identifier: BSD-3-Clause
"""Translate a plain-text word list into soju-import JSON using Ollama."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from soju import db, ollama_client
from soju.korean_levels import KoreanLevel, get_korean_level, list_level_ids
from soju.ollama_client import OllamaError
from soju.vocabulary_context import (
    build_vocabulary_context as _build_vocabulary_context,
)

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

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        text = strip_bullet(stripped)
        if not text:
            continue
        if SECTION_HEADER.match(text) and not db.has_hangul(text):
            continue

        arrow = ARROW_LINE.match(text)
        if arrow:
            entry = arrow.group(1).strip()
            hint = arrow.group(2).strip()
            if db.has_hangul(hint):
                hints.append(WordHint(raw, entry, hint_example=hint))
            else:
                hints.append(WordHint(raw, entry, hint_english=hint))
            continue

        parsed = db.parse_import_line(raw)
        if parsed:
            entry, example = parsed
            entry = strip_bullet(entry)
            if not db.has_hangul(entry):
                if example and db.has_hangul(example):
                    entry, example = example, entry
                else:
                    continue
            hint_english = None
            hint_example = None
            if example:
                if db.has_hangul(example):
                    hint_example = example
                else:
                    hint_english = example
            hints.append(WordHint(raw, entry, hint_english, hint_example))
            continue

        if not db.has_hangul(text):
            continue

        hints.append(WordHint(raw, text))

    return hints


def build_system_prompt(level: KoreanLevel, vocabulary_context: str) -> str:
    return f"""You are a Korean language lexicographer helping build a {level.label} learner vocabulary database.

Level guidance:
{level.guidance}

Use this existing vocabulary when writing example sentences. Prefer words and verbs from these lists over introducing new ones.

{vocabulary_context}

For each input item, produce one JSON record with:
- hangul: dictionary form in Korean (Hangul)
- romanization: Revised Romanization, lowercase, hyphenated syllables (e.g. hak-gyo, meo-geo-yo)
- english: concise English gloss
- type: one of noun, verb, adjective, adverb, pronoun
- examples: optional array of 0-2 objects with hangul and english full-sentence examples

Rules:
- Honor any provided English hint or example hint from the input.
- Verbs/adjectives ending in -다 should use type verb or adjective appropriately.
- Grammar particles/suffixes (e.g. -도, -하고) are usually adverb or noun as appropriate.
- Example sentences should be natural beginner Korean and reuse known vocabulary when possible.
- If the input is already a full Korean sentence/expression, treat it as hangul with examples when helpful.
- Do not invent registry duplicates; translate only the requested items.

Respond with valid JSON only using this shape:
{{"records": [{{"hangul": "...", "romanization": "...", "english": "...", "type": "...", "examples": [{{"hangul": "...", "english": "..."}}]}}]}}"""


def build_user_prompt(batch: list[WordHint]) -> str:
    items = []
    for index, hint in enumerate(batch, start=1):
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

    clean: dict[str, Any] = {
        "hangul": db.normalize_hangul(str(record["hangul"])),
        "romanization": str(record["romanization"]).strip().lower(),
        "english": db.normalize_english_gloss(str(record["english"])),
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
                    "hangul": db.normalize_hangul(str(example["hangul"])),
                    "english": db.normalize_english(str(example["english"])),
                }
            )
        if parsed_examples:
            clean["examples"] = parsed_examples

    return clean


def translate_batch(
    batch: list[WordHint],
    *,
    level: KoreanLevel,
    vocabulary_context: str,
    model: str,
    base_url: str,
    temperature: float,
) -> list[dict[str, Any]]:
    content = ollama_client.chat(
        [
            {
                "role": "system",
                "content": build_system_prompt(level, vocabulary_context),
            },
            {"role": "user", "content": build_user_prompt(batch)},
        ],
        model=model,
        base_url=base_url,
        json_mode=True,
        temperature=temperature,
    )

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned invalid JSON: {exc}") from exc

    records = payload.get("records") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("Model JSON must contain a records array.")

    cleaned: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        normalized = normalize_record(record)
        if normalized:
            cleaned.append(normalized)
    return cleaned


def translate_words(
    lines: list[str],
    *,
    model: str,
    base_url: str,
    batch_size: int,
    temperature: float,
    skip_existing: bool,
    level_id: str | None,
    root=None,
) -> tuple[list[dict[str, Any]], list[str]]:
    hints = parse_word_list_lines(lines)
    if not hints:
        return [], ["No translatable lines found in input."]

    level = get_korean_level(level_id, root)
    vocabulary_context = _build_vocabulary_context(root, compact=False, level=level)
    existing = db.vocabulary_by_sense(root) if skip_existing else {}
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen: set[tuple[str, str]] = set()

    for start in range(0, len(hints), batch_size):
        batch = hints[start : start + batch_size]
        batch_records = translate_batch(
            batch,
            level=level,
            vocabulary_context=vocabulary_context,
            model=model,
            base_url=base_url,
            temperature=temperature,
        )

        if len(batch_records) != len(batch):
            warnings.append(f"Batch {start // batch_size + 1}: expected {len(batch)} records, got {len(batch_records)}.")

        for hint, record in zip(batch, batch_records, strict=False):
            key = db.sense_key(record["hangul"], record["english"])
            if skip_existing and key in existing:
                warnings.append(f"Skipped existing registry entry: {record['hangul']} ({record['english']})")
                continue
            if key in seen:
                warnings.append(f"Skipped duplicate in output: {record['hangul']} ({record['english']})")
                continue
            seen.add(key)
            records.append(record)

    return records, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Translate a plain-text word list into soju-import JSON via Ollama.")
    parser.add_argument("--file", "-f", required=True, help="Plain-text word list file")
    parser.add_argument("--output", "-o", help="Write JSON to this file instead of stdout")
    parser.add_argument("--model", default=ollama_client.DEFAULT_MODEL, help="Ollama model name")
    parser.add_argument("--base-url", default=ollama_client.DEFAULT_BASE_URL, help="Ollama base URL")
    parser.add_argument("--batch-size", type=int, default=8, help="Lines per Ollama request")
    parser.add_argument("--temperature", type=float, default=0.3, help="Sampling temperature")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Omit entries already in the registry",
    )
    parser.add_argument(
        "--level",
        default=None,
        help=f"Korean course level (default: SOJU_KOREAN_LEVEL or 1A). Known: {', '.join(list_level_ids())}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse input and print summary without calling Ollama",
    )
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    lines = path.read_text(encoding="utf-8").splitlines()
    hints = parse_word_list_lines(lines)

    if args.dry_run:
        level = get_korean_level(args.level)
        print(f"Korean level: {level.label} ({level.id})", file=sys.stderr)
        print(f"Parsed {len(hints)} translatable lines from {path}.", file=sys.stderr)
        for hint in hints:
            parts = [hint.entry]
            if hint.hint_english:
                parts.append(f"en={hint.hint_english}")
            if hint.hint_example:
                parts.append(f"ex={hint.hint_example}")
            print("  " + " | ".join(parts), file=sys.stderr)
        return 0

    if not ollama_client.check_available(args.base_url):
        print(
            f"Error: Ollama is not reachable at {args.base_url}. Start Ollama or run: docker compose --profile ollama up ollama ollama-pull",
            file=sys.stderr,
        )
        return 1

    try:
        records, warnings = translate_words(
            lines,
            model=args.model,
            base_url=args.base_url,
            batch_size=max(1, args.batch_size),
            temperature=args.temperature,
            skip_existing=args.skip_existing,
            level_id=args.level,
        )
    except (OllamaError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    payload = {"records": records}
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote {len(records)} records to {args.output}.", file=sys.stderr)
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
