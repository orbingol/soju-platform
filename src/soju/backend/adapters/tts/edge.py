# SPDX-License-Identifier: BSD-3-Clause
"""Microsoft Edge neural TTS via ``edge-tts``."""

from __future__ import annotations

import tempfile
from pathlib import Path

import edge_tts

from soju.backend.abstract.tts import TtsError


def speed_to_edge_rate(speed: float) -> str:
    """Map a Soju speed multiplier to an edge-tts rate string (e.g. ``+20%``)."""
    # edge-tts expects e.g. "+20%" / "-30%"; Soju slider is typically 0.25–1.5.
    percent = int(round((speed - 1.0) * 100))
    percent = max(-50, min(100, percent))
    return f"{percent:+d}%"


class EdgeTtsEngine:
    """Synthesize MP3 audio with Microsoft Edge neural voices (network required)."""

    def __init__(self, *, default_voice: str = "ko-KR-SunHiNeural") -> None:
        self._default_voice = default_voice.strip() or "ko-KR-SunHiNeural"

    @property
    def name(self) -> str:
        return "edge"

    async def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        speed: float = 1.0,
    ) -> tuple[bytes, str]:
        use_voice = (voice or self._default_voice).strip() or self._default_voice
        try:
            with tempfile.TemporaryDirectory() as tmp:
                out_path = Path(tmp) / "speech.mp3"
                communicate = edge_tts.Communicate(text, use_voice, rate=speed_to_edge_rate(speed))
                await communicate.save(str(out_path))
                audio = out_path.read_bytes()
        except TtsError:
            raise
        except Exception as exc:  # noqa: BLE001 - surface provider errors to the route layer
            raise TtsError(str(exc) or "edge-tts failed") from exc

        return audio, "audio/mpeg"

    async def aclose(self) -> None:
        return None
