# SPDX-License-Identifier: BSD-3-Clause
"""OpenAI-ish speech request models for ``POST /v1/audio/speech``."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SpeechRequest(BaseModel):
    """Body accepted by the Soju TTS speech endpoint (Piper / OpenAI-compatible)."""

    input: str | list[str] | None = None
    text: str | None = None
    model: str | None = None
    voice: str | None = None
    speed: float = Field(default=1.0, gt=0.1, le=3.0)


def resolve_text(body: SpeechRequest) -> str:
    """Extract and strip speech text from ``input`` or ``text``."""
    if isinstance(body.input, list):
        text = "\n".join(part for part in body.input if part)
    elif isinstance(body.input, str):
        text = body.input
    else:
        text = body.text or ""
    return text.strip()


def resolve_voice(body: SpeechRequest, default: str) -> str:
    """Prefer ``voice``, then ``model``, then ``default``."""
    candidate = (body.voice or body.model or default).strip()
    return candidate or default
