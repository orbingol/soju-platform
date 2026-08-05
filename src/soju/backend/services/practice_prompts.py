# SPDX-License-Identifier: BSD-3-Clause
"""Practice prompt assembly, content policy, and light topic screening."""

from __future__ import annotations

import re
from typing import Any, Literal

PracticeExerciseType = Literal["sentences", "questions", "fill_in_blank", "story", "vocabulary_candidates"]

CONTENT_POLICY = """\
Content policy (education app for learners under 18):
- Keep topics and stories wholesome and age-appropriate.
- Do NOT include sexual content, romance that is explicit, fighting, violence, gore, guns/weapons, crime how-tos, or self-harm.
- If a theme or topic would go there, redirect to a wholesome everyday alternative (school, hobbies, food, travel, family, daily routines).
"""

# Obvious English (and a few Korean) phrases — defense in depth before the LLM.
_BLOCKLIST_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bporn\b",
        r"\bsex\b",
        r"\bsexual\b",
        r"\bnude\b",
        r"\bnaked\b",
        r"\berotic\b",
        r"\bgun\b",
        r"\bguns\b",
        r"\bpistol\b",
        r"\brifle\b",
        r"\bshoot(?:ing|er)?\b",
        r"\bkill(?:ing|ed)?\b",
        r"\bmurder\b",
        r"\bstab(?:bing|bed)?\b",
        r"\bblood(?:y)?\b",
        r"\bgore\b",
        r"\bviolence\b",
        r"\bviolent\b",
        r"\bfight(?:ing|s)?\b",
        r"\bsuicide\b",
        r"\bself[- ]?harm\b",
        r"성관계",
        r"총기",
        r"살인",
        r"자살",
    )
)

CANDIDATES_OPTIONAL = (
    '"vocabulary_candidates" is optional: at most 3 new words related to the theme '
    "(hangul + english only; no romanization); omit the field entirely if none fit."
)


class PracticeTopicBlockedError(Exception):
    """Raised when theme/topic fails the light content blocklist."""


def screen_practice_text(*parts: str) -> None:
    """Raise :class:`PracticeTopicBlockedError` when blocked phrases appear."""
    blob = "\n".join(part.strip() for part in parts if part and part.strip())
    if not blob:
        return
    for pattern in _BLOCKLIST_PATTERNS:
        if pattern.search(blob):
            raise PracticeTopicBlockedError(
                "That topic is not appropriate for this education app. "
                "Please try a different, everyday theme (school, food, travel, hobbies, family)."
            )


def _response_spec(exercise_type: PracticeExerciseType, count: int) -> tuple[str, list[str]]:
    if exercise_type == "sentences":
        return (
            '{\n  "sentences": [{"hangul": "...", "english": "..."}],\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
            [
                f'Exactly {count} beginner sentence(s) in "sentences".',
                "Each hangul value must be exactly one simple sentence (no multi-sentence stories, no clause chains).",
                CANDIDATES_OPTIONAL,
            ],
        )
    if exercise_type == "questions":
        return (
            '{\n  "questions": [{"prompt": "...", "answer": "...", "english": "..."}],\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
            [
                f'Exactly {count} beginner question(s) in "questions".',
                'Each item needs "prompt" (a direct question in Korean hangul only), "answer" (what the learner should produce in Korean), and "english" (English gloss of the prompt for a Translate button).',
                'Do NOT put English inside "prompt" (no parentheses glosses). Do NOT use speaker labels like "A:" or "B:", and do not write A–B dialogues.',
                CANDIDATES_OPTIONAL,
            ],
        )
    if exercise_type == "fill_in_blank":
        return (
            '{\n  "fill_in_blank": [{"prompt": "카페에서 ___ 주세요", "answer": "커피", "english": "Please give me coffee at the café"}],\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
            [
                f'Exactly {count} fill-in-the-blank item(s) in "fill_in_blank".',
                'Every "prompt" MUST contain the exact blank marker ___ (three underscores) exactly once — this is mandatory.',
                'Write 1–2 natural Korean sentences in hangul only; leave the missing word/phrase as ___; put the missing text in "answer"; put an English gloss of the full prompt in "english".',
                'Do NOT fill the blank with the answer in "prompt". Do NOT put English inside "prompt". Do NOT use speaker labels like "A:" or "B:".',
                CANDIDATES_OPTIONAL,
            ],
        )
    if exercise_type == "story":
        return (
            '{\n  "story": {"title": "...", "sentences": [{"hangul": "...", "english": "..."}]},\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
            [
                f'One short first-person story in "story" with about {count} sentence(s) (aim for a paragraph of roughly 4–7 linked sentences; stay near {count}).',
                'The story prompt is a personal question the learner will answer (e.g. "What did you do last weekend?"). Write a model answer as a continuous narrative paragraph, not a list of unrelated lines.',
                "Do NOT write a dialogue, A–B conversation, interview, or Q&A. No speaker labels. No questions inside the story unless natural speech within one sentence.",
                'Each "sentences" item MUST be an object {"hangul":"...","english":"..."} — never a bare string.',
                "Stay at the learner level: simple connected ideas (who/where/what/why), like a short personal reply.",
                CANDIDATES_OPTIONAL,
            ],
        )
    return (
        '{\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
        [f'Exactly {count} vocabulary item(s) in "vocabulary_candidates" (hangul and english required; do not include romanization).'],
    )


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
) -> str:
    """Build the Practice generation system prompt (includes content policy)."""
    count = max(1, int(count))
    shape, requirements = _response_spec(exercise_type, count)
    story_topic_line = ""
    if exercise_type == "story" and story_topic and story_topic.strip():
        story_topic_line = f"\n\nStory prompt (personal question to answer in first person):\n{story_topic.strip()}"

    previous_block = ""
    regen_rule = ""
    if exercise_type == "story" and previous_story:
        sentences = previous_story.get("sentences") or []
        hangul_lines = " ".join(
            str(item.get("hangul", "")).strip() for item in sentences if isinstance(item, dict) and str(item.get("hangul", "")).strip()
        )
        if hangul_lines:
            title = str(previous_story.get("title") or "").strip()
            title_line = f"Title: {title}\n" if title else ""
            previous_block = (
                "\n\nPrevious sample (do NOT reuse — write a clearly different story with a new title and different events/details):\n"
                f"{title_line}{hangul_lines}"
            )
            regen_rule = "\n- This is a regeneration: invent a fresh narrative; do not copy or lightly paraphrase the previous sample."

    guidance_block = level_guidance
    if grammar_summary and grammar_summary.strip():
        guidance_block = f"{level_guidance}\n\n{grammar_summary.strip()}"

    requirement_lines = "\n".join(f"- {item}" for item in requirements)
    return f"""{CONTENT_POLICY}

You are a Korean language tutor creating a beginner practice session.

Learner level: {level_label}
{guidance_block}

Theme: {theme_text}{story_topic_line}{previous_block}

Prefer this vocabulary when it fits the theme (hangul only; do not invent unrelated words):
{_format_hangul(hangul)}

Prefer these grammar patterns for this level when they fit:
{_format_grammar(grammar)}

Respond with valid JSON only (no markdown prose) using this shape:
{shape}

Requirements:
{requirement_lines}
- Keep hangul natural and beginner-friendly.
- Do not include romanization fields anywhere in the JSON.{regen_rule}"""


def build_story_evaluate_prompt(
    *,
    level_label: str,
    level_guidance: str,
    grammar_summary: str | None,
    topic: str,
    user_story: str,
    model_story: str,
) -> str:
    """Build the story evaluate system prompt (includes content policy)."""
    guidance_block = level_guidance
    if grammar_summary and grammar_summary.strip():
        guidance_block = f"{level_guidance}\n\n{grammar_summary.strip()}"
    return f"""{CONTENT_POLICY}

You are a Korean language tutor giving brief feedback on a beginner's written story.

Learner level: {level_label}
{guidance_block}

Story prompt (personal question the learner answered):
{topic}

Model reference story (for comparison only; do not demand the learner match it word-for-word):
{model_story}

Learner's story:
{user_story}

Respond with valid JSON only (no markdown prose) using this shape:
{{"feedback": "..."}}

Requirements:
- "feedback" must be short English feedback only (2–4 sentences).
- Judge whether the learner answered the prompt as a short first-person narrative (not a dialogue).
- Mention grammar or vocabulary gently when useful.
- Do not rewrite the whole story; at most quote a tiny suggested fix.
- Do not include Korean romanization."""
