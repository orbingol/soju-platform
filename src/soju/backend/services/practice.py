# SPDX-License-Identifier: BSD-3-Clause
"""Practice generate / evaluate application service (embed + retrieve + LLM)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from soju.backend.abstract.llm import LlmProviderError
from soju.backend.config.settings import LlmSettings
from soju.backend.services.llm import LlmProxyService
from soju.backend.services.practice_prompts import (
    PracticeExerciseType,
    PracticeTopicBlockedError,
    build_practice_system_prompt,
    build_story_evaluate_prompt,
    build_story_topic_prompt,
    screen_practice_text,
)
from soju.backend.services.practice_session import (
    PracticeSessionParseError,
    parse_feedback_json,
    parse_practice_session_json,
    parse_story_topic_json,
)
from soju.levels import get_language_level, load_levels_config
from soju.prompts.loader import get_prompts
from soju.prompts.models import PromptsSettings
from soju.services.embeddings.retrieve import PracticeRetrieveError, retrieve_practice

PRACTICE_BASE_MAX_TOKENS = 600
PRACTICE_TOKENS_PER_ITEM = 180
PRACTICE_MAX_TOKENS_CAP = 4000
EVALUATE_MAX_TOKENS = 800
STORY_TOPIC_MAX_TOKENS = 200
STORY_TOPIC_MAX_ATTEMPTS = 2


class PracticeServiceError(Exception):
    """Practice service failure with HTTP status."""

    def __init__(self, message: str, status: int = 500) -> None:
        super().__init__(message)
        self.status = status


def _estimate_max_tokens(count: int) -> int:
    return min(PRACTICE_MAX_TOKENS_CAP, PRACTICE_BASE_MAX_TOKENS + max(1, count) * PRACTICE_TOKENS_PER_ITEM)


def _level_grammar_summary(level_id: str, root: Path | None) -> str | None:
    config = load_levels_config(root)
    entry = config.get("levels", {}).get(level_id, {})
    if not isinstance(entry, dict):
        return None
    summary = str(entry.get("grammar_summary") or "").strip()
    return summary or None


def _extract_message_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content
    text = first.get("text")
    return text if isinstance(text, str) else ""


def _extract_embedding(payload: dict[str, Any]) -> list[float]:
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise PracticeServiceError("Embeddings response missing data", 502)
    first = data[0]
    if not isinstance(first, dict):
        raise PracticeServiceError("Embeddings response missing vector", 502)
    embedding = first.get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise PracticeServiceError("Embeddings response missing vector", 502)
    try:
        return [float(value) for value in embedding]
    except (TypeError, ValueError) as exc:
        raise PracticeServiceError("Embeddings response contained a non-numeric vector", 502) from exc


class PracticeService:
    """Embed theme text, retrieve cache rows, and generate/evaluate practice sessions."""

    def __init__(
        self,
        llm: LlmProxyService,
        settings: LlmSettings,
        *,
        data_root: Path | None = None,
        prompts: PromptsSettings | None = None,
    ) -> None:
        self._llm = llm
        self._settings = settings
        self._data_root = data_root
        self._prompts = prompts or get_prompts()

    async def _embed_text(self, text: str) -> list[float]:
        try:
            payload = await self._llm.embeddings(
                {
                    "model": self._settings.embed_model,
                    "input": text,
                }
            )
        except LlmProviderError as exc:
            raise PracticeServiceError(f"Embedding failed: {exc}", 502) from exc
        return _extract_embedding(payload)

    async def _complete_json(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        body = {
            "model": self._settings.chat_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "reasoning_effort": "none",
        }
        try:
            payload = await self._llm.chat_completions(body, stream=False)
        except LlmProviderError as exc:
            raise PracticeServiceError(f"LLM completion failed: {exc}", 502) from exc
        if not isinstance(payload, dict):
            raise PracticeServiceError("LLM completion did not return JSON", 502)
        return _extract_message_content(payload)

    async def generate(
        self,
        *,
        level_id: str,
        theme_text: str,
        exercise_type: PracticeExerciseType,
        count: int,
        include_unassigned: bool = False,
        story_topic: str | None = None,
        previous_story: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Embed + retrieve + generate a practice session JSON object."""
        theme = theme_text.strip()
        if not theme:
            raise PracticeServiceError("theme_text is required", 400)
        if exercise_type == "story" and not (story_topic or "").strip():
            raise PracticeServiceError("story_topic is required for story exercises", 400)

        try:
            screen_practice_text(theme, story_topic or "", prompts=self._prompts)
        except PracticeTopicBlockedError as exc:
            raise PracticeServiceError(str(exc), 400) from exc

        try:
            level = get_language_level(level_id, self._data_root)
        except ValueError as exc:
            raise PracticeServiceError(str(exc), 400) from exc
        grammar_summary = _level_grammar_summary(level.id, self._data_root)

        embed_text = f"{theme}\n{(story_topic or '').strip()}" if exercise_type == "story" else theme
        query_vector = await self._embed_text(embed_text)
        try:
            retrieved = retrieve_practice(
                query_vector=query_vector,
                level=level.id,
                include_unassigned=include_unassigned,
                root=self._data_root,
            )
        except PracticeRetrieveError as exc:
            raise PracticeServiceError(str(exc), exc.status) from exc

        regenerating = bool(previous_story and (previous_story.get("sentences") or []))
        system = build_practice_system_prompt(
            level_label=level.label,
            level_guidance=level.guidance,
            grammar_summary=grammar_summary,
            theme_text=theme,
            exercise_type=exercise_type,
            count=count,
            hangul=retrieved.hangul,
            grammar=[item.as_dict() for item in retrieved.grammar],
            story_topic=story_topic,
            previous_story=previous_story if regenerating else None,
            prompts=self._prompts,
        )
        user = self._prompts.practice.user_regenerate if regenerating else self._prompts.practice.user_generate
        content = await self._complete_json(
            system=system,
            user=user,
            temperature=0.9 if regenerating else 0.6,
            max_tokens=_estimate_max_tokens(count),
        )
        if not content.strip():
            raise PracticeServiceError(
                "The model returned an empty response. If you use a thinking model (e.g. gemma4), retry — "
                "Practice disables thinking for JSON generation. Otherwise try a smaller count.",
                502,
            )
        try:
            return parse_practice_session_json(content)
        except PracticeSessionParseError as exc:
            raise PracticeServiceError(str(exc), 502) from exc

    async def evaluate_story(
        self,
        *,
        level_id: str,
        topic: str,
        user_story: str,
        model_story: str,
    ) -> dict[str, str]:
        """Evaluate a learner story against a model reference."""
        draft = user_story.strip()
        if not draft:
            raise PracticeServiceError("user_story is required", 400)
        topic_text = topic.strip() or "Untitled"
        model_text = model_story.strip()
        if not model_text:
            raise PracticeServiceError("model_story is required", 400)

        try:
            screen_practice_text(topic_text, draft, prompts=self._prompts)
        except PracticeTopicBlockedError as exc:
            raise PracticeServiceError(str(exc), 400) from exc

        try:
            level = get_language_level(level_id, self._data_root)
        except ValueError as exc:
            raise PracticeServiceError(str(exc), 400) from exc
        grammar_summary = _level_grammar_summary(level.id, self._data_root)

        system = build_story_evaluate_prompt(
            level_label=level.label,
            level_guidance=level.guidance,
            grammar_summary=grammar_summary,
            topic=topic_text,
            user_story=draft,
            model_story=model_text,
            prompts=self._prompts,
        )
        content = await self._complete_json(
            system=system,
            user=self._prompts.practice.user_evaluate,
            temperature=0.4,
            max_tokens=EVALUATE_MAX_TOKENS,
        )
        try:
            return parse_feedback_json(content)
        except PracticeSessionParseError as exc:
            raise PracticeServiceError(str(exc), 502) from exc

    async def generate_story_topic(
        self,
        *,
        level_id: str,
        theme_text: str,
        previous_topic: str | None = None,
    ) -> dict[str, str]:
        """Generate one age-appropriate story prompt for the given theme."""
        theme = theme_text.strip()
        if not theme:
            raise PracticeServiceError("theme_text is required", 400)

        try:
            screen_practice_text(theme, prompts=self._prompts)
        except PracticeTopicBlockedError as exc:
            raise PracticeServiceError(str(exc), 400) from exc

        try:
            level = get_language_level(level_id, self._data_root)
        except ValueError as exc:
            raise PracticeServiceError(str(exc), 400) from exc

        system = build_story_topic_prompt(
            level_label=level.label,
            level_guidance=level.guidance,
            theme_text=theme,
            previous_topic=previous_topic,
            prompts=self._prompts,
        )
        last_error = self._prompts.practice.story_topic_failed
        for attempt in range(STORY_TOPIC_MAX_ATTEMPTS):
            user = (
                self._prompts.practice.user_story_topic_retry
                if attempt > 0
                else self._prompts.practice.user_story_topic
            )
            content = await self._complete_json(
                system=system,
                user=user,
                temperature=0.7 if attempt == 0 else 0.85,
                max_tokens=STORY_TOPIC_MAX_TOKENS,
            )
            try:
                topic = parse_story_topic_json(content)
            except PracticeSessionParseError as exc:
                last_error = str(exc)
                continue
            try:
                screen_practice_text(topic, prompts=self._prompts)
            except PracticeTopicBlockedError:
                last_error = self._prompts.practice.story_topic_unsafe
                continue
            return {"topic": topic}
        raise PracticeServiceError(last_error, 502)
