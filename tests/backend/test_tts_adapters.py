# SPDX-License-Identifier: BSD-3-Clause
"""TTS adapters (mocked edge-tts; piper misconfig)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("edge_tts")

from soju.backend.abstract.tts import TtsError
from soju.backend.adapters.tts import build_tts_engine
from soju.backend.adapters.tts.edge import EdgeTtsEngine, speed_to_edge_rate
from soju.backend.adapters.tts.piper import PiperTtsEngine
from soju.backend.config import PiperTtsSettings, TtsSettings


def test_speed_to_edge_rate() -> None:
    assert speed_to_edge_rate(1.0) == "+0%"
    assert speed_to_edge_rate(1.2) == "+20%"
    assert speed_to_edge_rate(0.5) == "-50%"


def test_build_tts_engine_edge() -> None:
    engine = build_tts_engine(TtsSettings(engine="edge", voice="ko-KR-SunHiNeural"))
    assert isinstance(engine, EdgeTtsEngine)
    assert engine.name == "edge"


def test_piper_requires_model_path() -> None:
    with pytest.raises(TtsError, match="model_path"):
        PiperTtsEngine(model_path=None)


def test_piper_missing_file(tmp_path: Path) -> None:
    with pytest.raises(TtsError, match="not found"):
        PiperTtsEngine(model_path=str(tmp_path / "missing.onnx"))


def test_edge_synthesize_mp3() -> None:
    engine = EdgeTtsEngine(default_voice="ko-KR-SunHiNeural")
    communicate = MagicMock()
    communicate.save = AsyncMock(side_effect=lambda path: Path(path).write_bytes(b"ID3fake"))

    async def _run() -> tuple[bytes, str]:
        with patch("soju.backend.adapters.tts.edge.edge_tts.Communicate", return_value=communicate):
            return await engine.synthesize("안녕", speed=1.0)

    audio, media_type = asyncio.run(_run())
    assert audio == b"ID3fake"
    assert media_type == "audio/mpeg"
    communicate.save.assert_awaited()


def test_build_tts_engine_piper(tmp_path: Path) -> None:
    model = tmp_path / "voice.onnx"
    model.write_bytes(b"onnx")
    engine = build_tts_engine(
        TtsSettings(engine="piper", piper=PiperTtsSettings(model_path=str(model))),
    )
    assert engine.name == "piper"
