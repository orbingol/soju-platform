# SPDX-License-Identifier: BSD-3-Clause
"""Korean LLM system prompts (translation and example generation)."""

from __future__ import annotations

from soju.levels import LanguageLevel


def translation_system_prompt(level: LanguageLevel, vocab_context: str) -> str:
    """System prompt for batch vocabulary translation via an LLM.

    Args:
        level: Active course level (label + guidance).
        vocab_context: Formatted existing vocabulary for the model to reuse.

    Returns:
        The full system prompt string.
    """
    return f"""You are a Korean language lexicographer helping build a {level.label} learner vocabulary database.

Level guidance:
{level.guidance}

Use this existing vocabulary when writing example sentences. Prefer words and verbs from these lists over introducing new ones.

{vocab_context}

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


def _verb_batch_json_schema(examples_per: int) -> str:
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


def verb_examples_system_prompt(
    level: LanguageLevel,
    vocab_context: str,
    *,
    examples_per: int,
) -> str:
    """System prompt for batch verb example generation."""
    return f"""You write Korean example sentences for a {level.label} learner app.

Level guidance:
{level.guidance}

{vocab_context}

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

{_verb_batch_json_schema(examples_per)}"""


def noun_examples_system_prompt(
    level: LanguageLevel,
    vocab_context: str,
    *,
    examples_per: int,
) -> str:
    """System prompt for batch noun example generation."""
    return f"""You write Korean example sentences for a {level.label} learner app.

Level guidance:
{level.guidance}

{vocab_context}

For each noun, write {examples_per} natural example sentence(s) using the word in a real situation with other vocabulary from the list above.
Each example should add context (where, with whom, why) — not just "This is X" or "I have X" repeated with different time words.
Return one object per input noun using the exact id from the input.
English must be natural and must NOT include parenthetical register notes.

Return ONLY valid JSON (no markdown fences, no prose):
{{"entries": [{{"id": "<uuid>", "examples": [{{"hangul": "...", "english": "..."}}]}}]}}"""
