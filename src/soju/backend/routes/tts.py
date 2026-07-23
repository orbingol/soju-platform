# SPDX-License-Identifier: BSD-3-Clause
"""TTS speech endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from soju.backend.abstract.tts import TtsError
from soju.backend.models.speech import SpeechRequest, resolve_text, resolve_voice
from soju.backend.services import AppServices, get_services

router = APIRouter(tags=["tts"])


@router.post("/v1/audio/speech")
async def synthesize(
    body: SpeechRequest,
    services: Annotated[AppServices, Depends(get_services)],
) -> Response:
    """Synthesize speech and return raw audio bytes."""
    text = resolve_text(body)
    if not text:
        raise HTTPException(status_code=400, detail="Missing input text")

    voice = resolve_voice(body, services.settings.tts.voice)
    try:
        audio, media_type = await services.tts.synthesize(text, voice=voice, speed=body.speed)
    except TtsError as exc:
        raise HTTPException(status_code=502, detail=str(exc) or "TTS failed") from exc

    if not audio:
        raise HTTPException(status_code=502, detail="TTS returned empty audio")
    return Response(content=audio, media_type=media_type)
