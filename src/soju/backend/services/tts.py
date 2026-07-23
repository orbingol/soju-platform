# SPDX-License-Identifier: BSD-3-Clause
"""Application service: speech synthesis over a TTS adapter."""

from __future__ import annotations

from soju.backend.abstract.tts import TtsEngine, TtsError
from soju.backend.models.speech import SpeechRequest, resolve_text, resolve_voice


class TtsService:
    """Application service wrapping an :class:`~soju.backend.abstract.tts.TtsEngine`."""

    def __init__(self, engine: TtsEngine, *, default_voice: str) -> None:
        self._engine = engine
        self._default_voice = default_voice

    @property
    def name(self) -> str:
        return self._engine.name

    async def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        speed: float = 1.0,
    ) -> tuple[bytes, str]:
        use_voice = voice or self._default_voice
        audio, media_type = await self._engine.synthesize(text, voice=use_voice, speed=speed)
        if not audio:
            raise TtsError("TTS returned empty audio")
        return audio, media_type

    async def synthesize_request(self, body: SpeechRequest) -> tuple[bytes, str]:
        """Resolve text/voice from ``body`` and synthesize.

        Raises:
            ValueError: When the request has no usable input text (map to HTTP 400).
            TtsError: On synthesis failure or empty audio (map to HTTP 502).
        """
        text = resolve_text(body)
        if not text:
            raise ValueError("Missing input text")
        voice = resolve_voice(body, self._default_voice)
        return await self.synthesize(text, voice=voice, speed=body.speed)

    async def aclose(self) -> None:
        await self._engine.aclose()
