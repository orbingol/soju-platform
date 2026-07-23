# SPDX-License-Identifier: BSD-3-Clause
"""Pydantic settings models mirroring backend YAML config."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ServerSettings(BaseModel):
    """HTTP server bind address and browser CORS origins."""

    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:8080", "http://localhost:5173"],
    )


class LlmSettings(BaseModel):
    """Upstream LLM provider (OpenAI-compatible facade target)."""

    provider: Literal["ollama"] = "ollama"
    base_url: str = "http://localhost:11434"
    chat_model: str = "gemma4:e4b"
    embed_model: str = "nomic-embed-text"
    timeout_s: int = Field(default=600, ge=1)

    @field_validator("base_url")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        return value.strip().rstrip("/")


class PiperTtsSettings(BaseModel):
    """Native Piper options (used when ``tts.engine`` is ``piper``)."""

    model_path: str | None = None
    speaker: str | int | None = None


class TtsSettings(BaseModel):
    """Text-to-speech adapter selection and default voice."""

    engine: Literal["edge", "piper"] = "edge"
    voice: str = "ko-KR-SunHiNeural"
    piper: PiperTtsSettings = Field(default_factory=PiperTtsSettings)


class ClientSettings(BaseModel):
    """Non-secret values exposed to the web app via ``/v1/soju/client-config``."""

    ai_enabled: bool = True
    api_mode: Literal["chat-completions", "conversations"] = "chat-completions"
    tutor_name: str = "Hee-jae (희재)"
    system_prompt: str = ""
    chat_summary_trigger: int = Field(default=10, ge=1)
    chat_keep_recent: int = Field(default=6, ge=1)


class BackendSettings(BaseModel):
    """Root Soju backend configuration."""

    server: ServerSettings = Field(default_factory=ServerSettings)
    llm: LlmSettings = Field(default_factory=LlmSettings)
    tts: TtsSettings = Field(default_factory=TtsSettings)
    client: ClientSettings = Field(default_factory=ClientSettings)
