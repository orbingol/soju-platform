# SPDX-License-Identifier: BSD-3-Clause
"""Native Piper TTS via the ``piper`` CLI (optional Korean voice when configured)."""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

from soju.backend.abstract.tts import TtsError


class PiperTtsEngine:
    """Synthesize WAV audio with the Piper CLI and a configured ONNX voice model."""

    def __init__(
        self,
        *,
        model_path: str | None,
        speaker: str | int | None = None,
        default_voice: str | None = None,
        piper_bin: str = "piper",
    ) -> None:
        if not model_path or not str(model_path).strip():
            raise TtsError("Piper TTS requires tts.piper.model_path in backend config (path to a Piper ONNX voice model).")
        resolved = Path(model_path).expanduser()
        if not resolved.is_file():
            raise TtsError(f"Piper model file not found: {resolved}")
        self._model_path = resolved
        self._speaker = speaker
        self._piper_bin = piper_bin
        _ = default_voice  # Request/config voice name is informational; ONNX path selects the voice.

    @property
    def name(self) -> str:
        return "piper"

    def _length_scale(self, speed: float) -> float:
        """Map Soju speed (>1 faster) to Piper ``--length_scale`` (<1 faster)."""
        if speed <= 0:
            return 1.0
        # Clamp similarly to edge-tts practical range.
        speed = max(0.25, min(3.0, speed))
        return 1.0 / speed

    async def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        speed: float = 1.0,
    ) -> tuple[bytes, str]:
        _ = voice  # Piper voice is the ONNX model; request voice is ignored.
        piper = shutil.which(self._piper_bin)
        if piper is None:
            raise TtsError(f"Piper executable {self._piper_bin!r} not found on PATH. Install Piper or switch tts.engine to 'edge'.")

        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "speech.wav"
            cmd: list[str] = [
                piper,
                "--model",
                str(self._model_path),
                "--output_file",
                str(out_path),
                "--length_scale",
                f"{self._length_scale(speed):.4f}",
            ]
            if self._speaker is not None:
                cmd.extend(["--speaker", str(self._speaker)])

            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _stdout, stderr = await proc.communicate(input=text.encode("utf-8"))
            except OSError as exc:
                raise TtsError(f"Failed to run Piper: {exc}") from exc

            if proc.returncode != 0:
                detail = stderr.decode("utf-8", errors="replace").strip() or f"exit {proc.returncode}"
                raise TtsError(f"Piper synthesis failed: {detail}")

            if not out_path.is_file():
                raise TtsError("Piper did not produce an output file")
            return out_path.read_bytes(), "audio/wav"

    async def aclose(self) -> None:
        return None
