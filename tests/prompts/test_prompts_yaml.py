# SPDX-License-Identifier: BSD-3-Clause
"""Tests for shipped prompts.yaml loading and template rendering."""

from __future__ import annotations

from soju.backend.config.client import client_config_from_settings
from soju.backend.config.loader import load_settings
from soju.backend.services.practice_prompts import (
    PracticeTopicBlockedError,
    build_practice_system_prompt,
    build_story_topic_prompt,
    clear_practice_prompt_caches,
    screen_practice_text,
)
from soju.languages.korean import prompts as korean_prompts
from soju.levels import LanguageLevel
from soju.prompts.format import render
from soju.prompts.loader import load_prompts


def test_load_shipped_prompts() -> None:
    clear_practice_prompt_caches()
    prompts = load_prompts()
    assert "under 18" in prompts.content_policy.lower() or "S1" in prompts.content_policy
    assert "S12" in prompts.guardrails.blocked_categories
    assert prompts.guardrails.category_patterns["S12"]
    assert "{{tutor_name}}" in prompts.chat.system
    assert prompts.chat.summarize
    assert prompts.practice.user_generate
    assert "sentences" in prompts.practice.exercises
    assert prompts.korean_cli.translation_system
    assert prompts.ui.disclaimer


def test_render_placeholder() -> None:
    assert render("Hello {{name}}", name="Soju") == "Hello Soju"


def test_backend_settings_include_prompts() -> None:
    settings = load_settings()
    assert settings.prompts.ui.disclaimer
    assert settings.client.system_prompt == ""
    cfg = client_config_from_settings(settings)
    assert settings.client.tutor_name in cfg.system_prompt
    assert cfg.chat_summarize_prompt
    assert cfg.ui_disclaimer == settings.prompts.ui.disclaimer
    assert "{{vocab_hint}}" in cfg.chat_vocab_suffix


def test_practice_prompts_from_yaml() -> None:
    clear_practice_prompt_caches()
    system = build_practice_system_prompt(
        level_label="1A",
        level_guidance="Use polite forms.",
        grammar_summary=None,
        theme_text="café",
        exercise_type="sentences",
        count=3,
        hangul=["커피"],
        grammar=[],
    )
    assert "café" in system or "cafe" in system.lower() or "Theme:" in system
    assert "under 18" in system.lower() or "Content policy" in system
    topic = build_story_topic_prompt(
        level_label="1A",
        level_guidance="Keep it simple.",
        theme_text="weekend",
        previous_topic="What did you do?",
    )
    assert "FORBIDDEN" in topic
    assert "weekend" in topic


def test_blocklist_from_yaml_patterns() -> None:
    clear_practice_prompt_caches()
    try:
        screen_practice_text("learn about guns and pistols")
        raised = False
    except PracticeTopicBlockedError:
        raised = True
    assert raised


def test_korean_translation_prompt_from_yaml() -> None:
    clear_practice_prompt_caches()
    level = LanguageLevel(
        id="1A",
        label="1A Beginner",
        description="Beginner",
        guidance="Keep sentences short.",
    )
    text = korean_prompts.translation_system_prompt(level, "커피: coffee")
    assert "lexicographer" in text
    assert "1A Beginner" in text
    assert "커피: coffee" in text
    user = korean_prompts.translation_user_prompt('{"items":[]}')
    assert "Translate these vocabulary items" in user
