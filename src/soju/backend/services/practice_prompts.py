# SPDX-License-Identifier: BSD-3-Clause
"""Practice prompt assembly, content policy, and light topic screening."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Literal

from soju.prompts.format import render
from soju.prompts.loader import get_prompts
from soju.prompts.models import PracticeExercisePrompt, PromptsSettings

PracticeExerciseType = Literal["sentences", "questions", "fill_in_blank", "story", "vocabulary_candidates"]


class PracticeTopicBlockedError(Exception):
    """Raised when theme/topic fails the light content blocklist."""


@lru_cache(maxsize=1)
def _compiled_blocklist() -> tuple[tuple[re.Pattern[str], ...], str]:
    prompts = get_prompts()
    patterns: list[re.Pattern[str]] = []
    for category_id in prompts.guardrails.blocked_categories:
        for raw in prompts.guardrails.category_patterns.get(category_id, []):
            patterns.append(re.compile(raw, re.IGNORECASE))
    return tuple(patterns), prompts.practice.topic_blocked


def clear_practice_prompt_caches() -> None:
    """Clear cached prompts/blocklist (for tests that reload ``prompts.yaml``)."""
    get_prompts.cache_clear()
    _compiled_blocklist.cache_clear()


def screen_practice_text(*parts: str, prompts: PromptsSettings | None = None) -> None:
    """Raise :class:`PracticeTopicBlockedError` when blocked phrases appear."""
    blob = "\n".join(part.strip() for part in parts if part and part.strip())
    if not blob:
        return
    if prompts is None:
        compiled, message = _compiled_blocklist()
    else:
        compiled = tuple(
            re.compile(raw, re.IGNORECASE) for category_id in prompts.guardrails.blocked_categories for raw in prompts.guardrails.category_patterns.get(category_id, [])
        )
        message = prompts.practice.topic_blocked
    for pattern in compiled:
        if pattern.search(blob):
            raise PracticeTopicBlockedError(message)


def _response_spec(
    exercise_type: PracticeExerciseType,
    count: int,
    prompts: PromptsSettings,
) -> tuple[str, list[str]]:
    exercise = prompts.practice.exercises.get(exercise_type)
    if exercise is None:
        exercise = PracticeExercisePrompt()
    candidates = prompts.practice.candidates_optional
    shape = render(exercise.shape.strip(), count=count, candidates_optional=candidates)
    requirements = [render(item, count=count, candidates_optional=candidates) for item in exercise.requirements]
    return shape, requirements


def _format_hangul(hangul: list[str]) -> str:
    return ", ".join(hangul) if hangul else "(none retrieved — use general beginner vocabulary instead)"


def _format_grammar(grammar: list[dict[str, Any]]) -> str:
    if not grammar:
        return "(none retrieved)"
    lines: list[str] = []
    for pattern in grammar:
        form = pattern.get("form", "")
        english = pattern.get("english", "")
        summary = pattern.get("summary")
        suffix = f": {summary}" if summary else ""
        lines.append(f"- {form} ({english}){suffix}")
    return "\n".join(lines)


def build_practice_system_prompt(
    *,
    level_label: str,
    level_guidance: str,
    grammar_summary: str | None,
    theme_text: str,
    exercise_type: PracticeExerciseType,
    count: int,
    hangul: list[str],
    grammar: list[dict[str, Any]],
    story_topic: str | None = None,
    previous_story: dict[str, Any] | None = None,
    prompts: PromptsSettings | None = None,
) -> str:
    """Build the Practice generation system prompt (includes content policy)."""
    cfg = prompts or get_prompts()
    count = max(1, int(count))
    shape, requirements = _response_spec(exercise_type, count, cfg)
    story_topic_line = ""
    if exercise_type == "story" and story_topic and story_topic.strip():
        story_topic_line = f"\n\nStory prompt (personal question to answer in first person):\n{story_topic.strip()}"

    previous_block = ""
    regen_rule = ""
    if exercise_type == "story" and previous_story:
        sentences = previous_story.get("sentences") or []
        hangul_lines = " ".join(str(item.get("hangul", "")).strip() for item in sentences if isinstance(item, dict) and str(item.get("hangul", "")).strip())
        if hangul_lines:
            title = str(previous_story.get("title") or "").strip()
            title_line = f"Title: {title}\n" if title else ""
            previous_block = f"\n\nPrevious sample (do NOT reuse — write a clearly different story with a new title and different events/details):\n{title_line}{hangul_lines}"
            regen_rule = "\n- This is a regeneration: invent a fresh narrative; do not copy or lightly paraphrase the previous sample."

    guidance_block = level_guidance
    if grammar_summary and grammar_summary.strip():
        guidance_block = f"{level_guidance}\n\n{grammar_summary.strip()}"

    requirement_lines = "\n".join(f"- {item}" for item in requirements)
    return render(
        cfg.practice.system,
        content_policy=cfg.content_policy.strip(),
        level_label=level_label,
        guidance_block=guidance_block,
        theme_text=theme_text,
        story_topic_line=story_topic_line,
        previous_block=previous_block,
        hangul_list=_format_hangul(hangul),
        grammar_list=_format_grammar(grammar),
        shape=shape,
        requirement_lines=requirement_lines,
        regen_rule=regen_rule,
    ).strip()


def build_story_evaluate_prompt(
    *,
    level_label: str,
    level_guidance: str,
    grammar_summary: str | None,
    topic: str,
    user_story: str,
    model_story: str,
    prompts: PromptsSettings | None = None,
) -> str:
    """Build the story evaluate system prompt (includes content policy)."""
    cfg = prompts or get_prompts()
    guidance_block = level_guidance
    if grammar_summary and grammar_summary.strip():
        guidance_block = f"{level_guidance}\n\n{grammar_summary.strip()}"
    return render(
        cfg.practice.evaluate_story,
        content_policy=cfg.content_policy.strip(),
        level_label=level_label,
        guidance_block=guidance_block,
        topic=topic,
        model_story=model_story,
        user_story=user_story,
    ).strip()


def build_story_topic_prompt(
    *,
    level_label: str,
    level_guidance: str,
    theme_text: str,
    previous_topic: str | None = None,
    prompts: PromptsSettings | None = None,
) -> str:
    """Build a strict prompt for one age-appropriate story practice question."""
    cfg = prompts or get_prompts()
    previous_line = ""
    if previous_topic and previous_topic.strip():
        previous_line = f"\n\nDo NOT repeat or lightly rephrase this previous topic:\n{previous_topic.strip()}\nInvent a clearly different personal question."
    return render(
        cfg.practice.story_topic,
        content_policy=cfg.content_policy.strip(),
        level_label=level_label,
        level_guidance=level_guidance,
        theme_text=theme_text.strip(),
        previous_line=previous_line,
    ).strip()
