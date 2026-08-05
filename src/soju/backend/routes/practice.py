# SPDX-License-Identifier: BSD-3-Clause
"""Practice generate / evaluate HTTP routes."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from soju.backend.config.settings import BackendSettings
from soju.backend.services.deps import get_llm, get_settings
from soju.backend.services.llm import LlmProxyService
from soju.backend.services.practice import PracticeService, PracticeServiceError

router = APIRouter(tags=["practice"])

ExerciseType = Literal["sentences", "questions", "fill_in_blank", "story", "vocabulary_candidates"]


class PracticeGenerateRequest(BaseModel):
    """Browser request for a full practice session (backend embeds + retrieves)."""

    level: str = Field(min_length=1)
    theme_text: str = Field(min_length=1)
    exercise_type: ExerciseType
    count: int = Field(default=5, ge=1, le=20)
    include_unassigned: bool = False
    story_topic: str | None = None
    previous_story: dict[str, Any] | None = None


class PracticeEvaluateRequest(BaseModel):
    """Browser request to evaluate a learner story."""

    level: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    user_story: str = Field(min_length=1)
    model_story: str = Field(min_length=1)


class PracticeStoryTopicRequest(BaseModel):
    """Browser request for an AI-generated story prompt."""

    level: str = Field(min_length=1)
    theme_text: str = Field(min_length=1)
    previous_topic: str | None = None


def _practice_service(llm: LlmProxyService, settings: BackendSettings) -> PracticeService:
    return PracticeService(llm, settings.llm, prompts=settings.prompts)


def _raise_service_error(exc: PracticeServiceError) -> None:
    raise HTTPException(status_code=exc.status, detail=str(exc)) from exc


@router.post("/v1/soju/practice/generate")
async def practice_generate(
    body: PracticeGenerateRequest,
    llm: LlmProxyService = Depends(get_llm),
    settings: BackendSettings = Depends(get_settings),
) -> dict[str, Any]:
    """Embed theme/topic, retrieve vocab/grammar, and generate a practice session."""
    service = _practice_service(llm, settings)
    try:
        return await service.generate(
            level_id=body.level,
            theme_text=body.theme_text,
            exercise_type=body.exercise_type,
            count=body.count,
            include_unassigned=body.include_unassigned,
            story_topic=body.story_topic,
            previous_story=body.previous_story,
        )
    except PracticeServiceError as exc:
        _raise_service_error(exc)
        raise  # pragma: no cover


@router.post("/v1/soju/practice/evaluate-story")
async def practice_evaluate_story(
    body: PracticeEvaluateRequest,
    llm: LlmProxyService = Depends(get_llm),
    settings: BackendSettings = Depends(get_settings),
) -> dict[str, str]:
    """Evaluate a learner story against a model reference."""
    service = _practice_service(llm, settings)
    try:
        return await service.evaluate_story(
            level_id=body.level,
            topic=body.topic,
            user_story=body.user_story,
            model_story=body.model_story,
        )
    except PracticeServiceError as exc:
        _raise_service_error(exc)
        raise  # pragma: no cover


@router.post("/v1/soju/practice/story-topic")
async def practice_story_topic(
    body: PracticeStoryTopicRequest,
    llm: LlmProxyService = Depends(get_llm),
    settings: BackendSettings = Depends(get_settings),
) -> dict[str, str]:
    """Generate one age-appropriate story topic for the current theme."""
    service = _practice_service(llm, settings)
    try:
        return await service.generate_story_topic(
            level_id=body.level,
            theme_text=body.theme_text,
            previous_topic=body.previous_topic,
        )
    except PracticeServiceError as exc:
        _raise_service_error(exc)
        raise  # pragma: no cover
