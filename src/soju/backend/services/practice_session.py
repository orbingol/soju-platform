# SPDX-License-Identifier: BSD-3-Clause
"""Parse and lightly validate Practice session JSON from the LLM."""

from __future__ import annotations

import json
import re
from typing import Any


class PracticeSessionParseError(Exception):
    """Invalid practice JSON payload."""


_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _strip_fences(text: str) -> str:
    match = _FENCE_RE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def _require_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PracticeSessionParseError(f"Invalid practice JSON: {path} must be a non-empty string")
    return value.strip()


def _parse_sentence(value: Any, path: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise PracticeSessionParseError(f"Invalid practice JSON: {path} must be an object")
    return {
        "hangul": _require_string(value.get("hangul"), f"{path}.hangul"),
        "english": _require_string(value.get("english"), f"{path}.english"),
    }


def _parse_story_sentence(value: Any, path: str) -> dict[str, str]:
    if isinstance(value, str):
        hangul = value.strip()
        if not hangul:
            raise PracticeSessionParseError(f"Invalid practice JSON: {path} must be a non-empty string")
        return {"hangul": hangul, "english": ""}
    if not isinstance(value, dict):
        raise PracticeSessionParseError(f"Invalid practice JSON: {path} must be an object or string")
    hangul = _require_string(value.get("hangul"), f"{path}.hangul")
    english = value.get("english")
    if english is None or english == "":
        return {"hangul": hangul, "english": ""}
    if not isinstance(english, str):
        raise PracticeSessionParseError(f"Invalid practice JSON: {path}.english must be a string")
    return {"hangul": hangul, "english": english.strip()}


def _parse_candidates(value: Any) -> list[dict[str, str]] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise PracticeSessionParseError('Invalid practice JSON: "vocabulary_candidates" must be an array')
    out: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise PracticeSessionParseError(f"Invalid practice JSON: vocabulary_candidates[{index}] must be an object")
        out.append(
            {
                "hangul": _require_string(item.get("hangul"), f"vocabulary_candidates[{index}].hangul"),
                "english": _require_string(item.get("english"), f"vocabulary_candidates[{index}].english"),
            }
        )
    return out


def parse_practice_session_json(text: str) -> dict[str, Any]:
    """Parse LLM text into a practice session object."""
    trimmed = _strip_fences(text)
    if not trimmed:
        raise PracticeSessionParseError("The model returned an empty response.")
    try:
        parsed = json.loads(trimmed)
    except json.JSONDecodeError as exc:
        raise PracticeSessionParseError(f"Invalid practice JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise PracticeSessionParseError("Invalid practice JSON: root must be an object")

    session: dict[str, Any] = {}
    if "sentences" in parsed:
        raw = parsed["sentences"]
        if not isinstance(raw, list):
            raise PracticeSessionParseError('Invalid practice JSON: "sentences" must be an array')
        session["sentences"] = [_parse_sentence(item, f"sentences[{i}]") for i, item in enumerate(raw)]
    if "questions" in parsed:
        raw = parsed["questions"]
        if not isinstance(raw, list):
            raise PracticeSessionParseError('Invalid practice JSON: "questions" must be an array')
        questions = []
        for i, item in enumerate(raw):
            if not isinstance(item, dict):
                raise PracticeSessionParseError(f"Invalid practice JSON: questions[{i}] must be an object")
            entry = {
                "prompt": _require_string(item.get("prompt"), f"questions[{i}].prompt"),
                "answer": _require_string(item.get("answer"), f"questions[{i}].answer"),
            }
            english = item.get("english")
            if isinstance(english, str) and english.strip():
                entry["english"] = english.strip()
            questions.append(entry)
        session["questions"] = questions
    if "fill_in_blank" in parsed:
        raw = parsed["fill_in_blank"]
        if not isinstance(raw, list):
            raise PracticeSessionParseError('Invalid practice JSON: "fill_in_blank" must be an array')
        blanks = []
        for i, item in enumerate(raw):
            if not isinstance(item, dict):
                raise PracticeSessionParseError(f"Invalid practice JSON: fill_in_blank[{i}] must be an object")
            entry = {
                "prompt": _require_string(item.get("prompt"), f"fill_in_blank[{i}].prompt"),
                "answer": _require_string(item.get("answer"), f"fill_in_blank[{i}].answer"),
            }
            english = item.get("english")
            if isinstance(english, str) and english.strip():
                entry["english"] = english.strip()
            blanks.append(entry)
        session["fill_in_blank"] = blanks
    if "story" in parsed:
        story = parsed["story"]
        if not isinstance(story, dict):
            raise PracticeSessionParseError('Invalid practice JSON: "story" must be an object')
        sentences_raw = story.get("sentences")
        if not isinstance(sentences_raw, list) or not sentences_raw:
            raise PracticeSessionParseError("Invalid practice JSON: story.sentences must be a non-empty array")
        story_out: dict[str, Any] = {
            "sentences": [_parse_story_sentence(item, f"story.sentences[{i}]") for i, item in enumerate(sentences_raw)],
        }
        title = story.get("title")
        if isinstance(title, str) and title.strip():
            story_out["title"] = title.strip()
        session["story"] = story_out

    candidates = _parse_candidates(parsed.get("vocabulary_candidates"))
    if candidates is not None:
        session["vocabulary_candidates"] = candidates

    if not any(key in session for key in ("sentences", "questions", "fill_in_blank", "story", "vocabulary_candidates")):
        raise PracticeSessionParseError("Invalid practice JSON: missing primary exercise payload")
    return session


def parse_feedback_json(text: str) -> dict[str, str]:
    """Parse evaluate JSON into ``{feedback}``."""
    trimmed = _strip_fences(text)
    if not trimmed:
        raise PracticeSessionParseError("The model returned empty feedback. Retry evaluate.")
    try:
        parsed = json.loads(trimmed)
    except json.JSONDecodeError as exc:
        raise PracticeSessionParseError(f"Invalid evaluate JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise PracticeSessionParseError("Invalid evaluate JSON: root must be an object")
    feedback = parsed.get("feedback")
    if not isinstance(feedback, str) or not feedback.strip():
        raise PracticeSessionParseError("Invalid evaluate JSON: feedback must be a non-empty string")
    return {"feedback": feedback.strip()}


def parse_story_topic_json(text: str) -> str:
    """Parse story-topic JSON into a single cleaned topic string."""
    trimmed = _strip_fences(text)
    if not trimmed:
        raise PracticeSessionParseError("The model returned an empty topic.")
    try:
        parsed = json.loads(trimmed)
    except json.JSONDecodeError as exc:
        raise PracticeSessionParseError(f"Invalid topic JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise PracticeSessionParseError("Invalid topic JSON: root must be an object")
    topic = parsed.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        raise PracticeSessionParseError("Invalid topic JSON: topic must be a non-empty string")
    cleaned = " ".join(topic.strip().split())
    # One question only — drop coaching / second sentences after the first "?".
    if "?" in cleaned:
        cleaned = cleaned.split("?", 1)[0].strip() + "?"
    else:
        # No question mark: keep the first sentence only.
        cleaned = cleaned.split(".", 1)[0].strip()
    words = cleaned.rstrip("?").split()
    if len(words) > 14:
        cleaned = " ".join(words[:14]).rstrip(".,;") + "?"
    if len(cleaned) > 100:
        raise PracticeSessionParseError("Invalid topic JSON: topic is too long")
    return cleaned
