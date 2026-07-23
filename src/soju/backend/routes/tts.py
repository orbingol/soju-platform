# SPDX-License-Identifier: BSD-3-Clause
"""TTS speech endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from soju.backend.abstract.tts import TtsError
from soju.backend.models.speech import SpeechRequest
from soju.backend.routes._http import raise_tts_502
from soju.backend.services.deps import get_tts
from soju.backend.services.tts import TtsService

router = APIRouter(tags=["tts"])


@router.post("/v1/audio/speech")
async def synthesize(
    body: SpeechRequest,
    tts: Annotated[TtsService, Depends(get_tts)],
) -> Response:
    """Synthesize speech and return raw audio bytes."""
    try:
        audio, media_type = await tts.synthesize_request(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TtsError as exc:
        raise_tts_502(exc)
    return Response(content=audio, media_type=media_type)
