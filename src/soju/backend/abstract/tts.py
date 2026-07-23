# SPDX-License-Identifier: BSD-3-Clause
"""TTS engine protocol for Soju backend adapters."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class TtsError(Exception):
    """Raised when a TTS adapter fails or is misconfigured."""


@runtime_checkable
class TtsEngine(Protocol):
    """Async text-to-speech backend used by ``POST /v1/audio/speech``."""

    @property
    def name(self) -> str:
        """Engine id (``edge`` or ``piper``)."""
        ...

    async def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        speed: float = 1.0,
    ) -> tuple[bytes, str]:
        """Synthesize ``text`` and return ``(audio_bytes, media_type)``.

        Args:
            text: Non-empty utterance to speak.
            voice: Optional voice / model override; adapters fall back to config default.
            speed: Playback rate multiplier (typically ~0.25–1.5 from the web UI).

        Returns:
            Raw audio bytes and an HTTP media type (e.g. ``audio/mpeg``, ``audio/wav``).

        Raises:
            TtsError: On misconfiguration or synthesis failure.
        """
        ...

    async def aclose(self) -> None:
        """Release engine resources (default: no-op)."""
        ...
