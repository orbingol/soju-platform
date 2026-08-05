# SPDX-License-Identifier: BSD-3-Clause
"""Korean LLM system prompts (translation and example generation)."""

from __future__ import annotations

from soju.levels import LanguageLevel
from soju.prompts.format import render
from soju.prompts.loader import get_prompts


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


def translation_system_prompt(level: LanguageLevel, vocab_context: str) -> str:
    """System prompt for batch vocabulary translation via an LLM."""
    prompts = get_prompts()
    return render(
        prompts.korean_cli.translation_system,
        level_label=level.label,
        level_guidance=level.guidance,
        vocab_context=vocab_context,
    ).strip()


def translation_user_prompt(items_json: str) -> str:
    """User prompt for batch vocabulary translation."""
    prompts = get_prompts()
    return render(prompts.korean_cli.translation_user, items_json=items_json).strip()


def verb_examples_system_prompt(
    level: LanguageLevel,
    vocab_context: str,
    *,
    examples_per: int,
) -> str:
    """System prompt for batch verb example generation."""
    prompts = get_prompts()
    return render(
        prompts.korean_cli.verb_examples_system,
        level_label=level.label,
        level_guidance=level.guidance,
        vocab_context=vocab_context,
        examples_per=examples_per,
        json_schema=_verb_batch_json_schema(examples_per),
    ).strip()


def noun_examples_system_prompt(
    level: LanguageLevel,
    vocab_context: str,
    *,
    examples_per: int,
) -> str:
    """System prompt for batch noun example generation."""
    prompts = get_prompts()
    return render(
        prompts.korean_cli.noun_examples_system,
        level_label=level.label,
        level_guidance=level.guidance,
        vocab_context=vocab_context,
        examples_per=examples_per,
    ).strip()
