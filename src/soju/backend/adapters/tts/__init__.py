# SPDX-License-Identifier: BSD-3-Clause
"""TTS adapter factories and implementations."""

from __future__ import annotations

from soju.backend.abstract.tts import TtsEngine, TtsError
from soju.backend.adapters.tts.edge import EdgeTtsEngine
from soju.backend.adapters.tts.piper import PiperTtsEngine
from soju.backend.config import TtsSettings


def build_tts_engine(settings: TtsSettings) -> TtsEngine:
    """Construct the configured TTS adapter.

    Raises:
        TtsError: If ``settings.engine`` is unknown or piper is misconfigured at build time.
    """
    if settings.engine == "edge":
        return EdgeTtsEngine(default_voice=settings.voice)
    if settings.engine == "piper":
        return PiperTtsEngine(
            model_path=settings.piper.model_path,
            speaker=settings.piper.speaker,
            default_voice=settings.voice,
        )
    raise TtsError(f"Unknown TTS engine {settings.engine!r}; expected 'edge' or 'piper'")


__all__ = [
    "EdgeTtsEngine",
    "PiperTtsEngine",
    "build_tts_engine",
]
