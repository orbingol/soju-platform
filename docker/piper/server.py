#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
"""
Local TTS HTTP server with a Piper-compatible /v1/audio/speech endpoint.

Uses Microsoft Edge neural voices via edge-tts (needs network). Upstream Piper has
no usable Korean neural voice for stock piper-tts; espeak-ng is too robotic for
language learning, so this service defaults to ko-KR-SunHiNeural.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import edge_tts
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

HOST = os.environ.get("PIPER_HOST", "0.0.0.0")
PORT = int(os.environ.get("PIPER_PORT", "5000"))
DEFAULT_VOICE = os.environ.get("PIPER_VOICE", "ko-KR-SunHiNeural")

app = FastAPI(title="Soju local TTS", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SpeechRequest(BaseModel):
    input: str | list[str] | None = None
    text: str | None = None
    model: str | None = None
    voice: str | None = None
    speed: float = Field(default=1.0, gt=0.1, le=3.0)


def resolve_text(body: SpeechRequest) -> str:
    if isinstance(body.input, list):
        text = "\n".join(part for part in body.input if part)
    elif isinstance(body.input, str):
        text = body.input
    else:
        text = body.text or ""
    return text.strip()


def speed_to_edge_rate(speed: float) -> str:
    # edge-tts expects e.g. "+20%" / "-30%"; Soju slider is typically 0.25–1.5.
    percent = int(round((speed - 1.0) * 100))
    percent = max(-50, min(100, percent))
    return f"{percent:+d}%"


async def synthesize_mp3(text: str, voice: str, speed: float) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "speech.mp3"
        communicate = edge_tts.Communicate(text, voice, rate=speed_to_edge_rate(speed))
        await communicate.save(str(out_path))
        return out_path.read_bytes()


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "engine": "edge-tts",
        "voice": DEFAULT_VOICE,
        "note": "Neural Korean via edge-tts (network required)",
    }


@app.post("/v1/audio/speech")
async def synthesize(body: SpeechRequest) -> Response:
    text = resolve_text(body)
    if not text:
        raise HTTPException(status_code=400, detail="Missing input text")

    voice = (body.voice or body.model or DEFAULT_VOICE).strip() or DEFAULT_VOICE
    try:
        audio = await synthesize_mp3(text, voice, body.speed)
    except Exception as exc:  # noqa: BLE001 - surface TTS provider errors to the client
        raise HTTPException(status_code=502, detail=str(exc) or "edge-tts failed") from exc

    if not audio:
        raise HTTPException(status_code=502, detail="edge-tts returned empty audio")

    return Response(content=audio, media_type="audio/mpeg")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
