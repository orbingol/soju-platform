# SPDX-License-Identifier: BSD-3-Clause
"""Pydantic models for shipped ``prompts.yaml``."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GuardrailsSettings(BaseModel):
    """MLCommons / Llama Guard category ids plus keyword proxy patterns."""

    blocked_categories: list[str] = Field(default_factory=list)
    category_patterns: dict[str, list[str]] = Field(default_factory=dict)


class ChatPromptSettings(BaseModel):
    """Chat tutor prompts exposed to the browser via ``/v1/soju/config/client``."""

    system: str = ""
    vocab_suffix: str = "Known vocabulary includes: {{vocab_hint}}"
    summarize: str = ""


class PracticeExercisePrompt(BaseModel):
    """JSON shape + requirement lines for one practice exercise type."""

    shape: str = ""
    requirements: list[str] = Field(default_factory=list)


class PracticePromptSettings(BaseModel):
    """Practice generate / evaluate / story-topic templates and user lines."""

    system: str = ""
    user_generate: str = "Generate today's practice session JSON."
    user_regenerate: str = "Generate a different practice session JSON. Do not reuse the previous story."
    user_evaluate: str = "Evaluate the learner story and return JSON feedback."
    user_story_topic: str = "Generate one safe story topic JSON for this theme."
    user_story_topic_retry: str = "Generate one different safe story topic JSON."
    story_topic: str = ""
    story_topic_failed: str = "Could not generate a suitable story topic. Please try again."
    story_topic_unsafe: str = "Generated topic was not appropriate. Please try again."
    evaluate_story: str = ""
    candidates_optional: str = ""
    topic_blocked: str = "That topic is not appropriate for this education app. Please try a different, everyday theme (school, food, travel, hobbies, family)."
    exercises: dict[str, PracticeExercisePrompt] = Field(default_factory=dict)


class KoreanCliPromptSettings(BaseModel):
    """CLI translation / example-fill system and user templates."""

    translation_system: str = ""
    translation_user: str = "Translate these vocabulary items into records. Return one record per item, in the same order.\n{{items_json}}"
    verb_examples_system: str = ""
    noun_examples_system: str = ""


class UiPromptSettings(BaseModel):
    """Shared non-secret UI copy for AI features."""

    disclaimer: str = "AI can make mistakes. Please verify the output."


class PromptsSettings(BaseModel):
    """Root prompts document (AI-facing text only)."""

    content_policy: str = ""
    guardrails: GuardrailsSettings = Field(default_factory=GuardrailsSettings)
    chat: ChatPromptSettings = Field(default_factory=ChatPromptSettings)
    practice: PracticePromptSettings = Field(default_factory=PracticePromptSettings)
    korean_cli: KoreanCliPromptSettings = Field(default_factory=KoreanCliPromptSettings)
    ui: UiPromptSettings = Field(default_factory=UiPromptSettings)
