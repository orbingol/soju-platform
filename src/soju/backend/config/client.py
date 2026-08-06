# SPDX-License-Identifier: BSD-3-Clause
"""Public client bootstrap payload for the web app."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from soju.backend.config.settings import BackendSettings
from soju.prompts.format import render


class ClientConfigResponse(BaseModel):
    """Non-secret settings the browser needs after pointing at the Soju API."""

    ai_enabled: bool
    api_mode: Literal["chat-completions", "conversations"]
    chat_model: str
    embed_model: str
    tutor_name: str
    system_prompt: str
    chat_summarize_prompt: str = ""
    chat_vocab_suffix: str = "Known vocabulary includes: {{vocab_hint}}"
    ui_disclaimer: str = "AI can make mistakes. Please verify the output."
    chat_summary_trigger: int = Field(ge=1)
    chat_keep_recent: int = Field(ge=1)
    tts_default_voice: str
    tts_engine_label: Literal["local"] = "local"


def client_config_from_settings(settings: BackendSettings) -> ClientConfigResponse:
    """Build a :class:`ClientConfigResponse` from loaded backend settings."""
    tutor = settings.client.tutor_name
    system_template = settings.client.system_prompt.strip() or settings.prompts.chat.system
    return ClientConfigResponse(
        ai_enabled=settings.client.ai_enabled,
        api_mode=settings.client.api_mode,
        chat_model=settings.llm.chat_model,
        embed_model=settings.llm.embed_model,
        tutor_name=tutor,
        system_prompt=render(system_template, tutor_name=tutor).strip(),
        chat_summarize_prompt=settings.prompts.chat.summarize.strip(),
        chat_vocab_suffix=settings.prompts.chat.vocab_suffix,
        ui_disclaimer=settings.prompts.ui.disclaimer,
        chat_summary_trigger=settings.client.chat_summary_trigger,
        chat_keep_recent=settings.client.chat_keep_recent,
        tts_default_voice=settings.tts.voice,
        tts_engine_label="local",
    )
