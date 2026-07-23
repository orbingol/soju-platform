# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for backend application services."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest

pytest.importorskip("fastapi")

from soju.backend.abstract.llm import LlmProviderError
from soju.backend.abstract.tts import TtsError
from soju.backend.models.speech import SpeechRequest
from soju.backend.services.llm import LlmProxyService
from soju.backend.services.tts import TtsService


class FakeLlm:
    name = "fake-llm"

    def __init__(self) -> None:
        self.closed = 0

    async def list_models(self) -> dict[str, Any]:
        return {"object": "list", "data": [{"id": "fake"}]}

    async def chat_completions(
        self,
        body: dict[str, Any],
        *,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[bytes]:
        _ = body
        if stream:

            async def gen() -> AsyncIterator[bytes]:
                yield b"data: {}\n\n"

            return gen()
        return {"choices": [{"message": {"content": "ok"}}]}

    async def embeddings(self, body: dict[str, Any]) -> dict[str, Any]:
        _ = body
        return {"object": "list", "data": []}

    async def aclose(self) -> None:
        self.closed += 1


class FakeTts:
    name = "fake-tts"

    def __init__(self, *, audio: bytes = b"AUDIO") -> None:
        self.audio = audio
        self.last_voice: str | None = None
        self.closed = 0

    async def synthesize(self, text: str, *, voice: str | None = None, speed: float = 1.0) -> tuple[bytes, str]:
        _ = text, speed
        self.last_voice = voice
        return self.audio, "audio/mpeg"

    async def aclose(self) -> None:
        self.closed += 1


def test_llm_proxy_list_models_delegates() -> None:
    async def _run() -> None:
        service = LlmProxyService(FakeLlm())
        assert await service.list_models() == {"object": "list", "data": [{"id": "fake"}]}

    asyncio.run(_run())


def test_llm_proxy_chat_stream_and_json() -> None:
    async def _run() -> None:
        service = LlmProxyService(FakeLlm())
        json_result = await service.chat_completions({"messages": []}, stream=False)
        assert isinstance(json_result, dict)

        stream_result = await service.chat_completions({"messages": []}, stream=True)
        assert hasattr(stream_result, "__aiter__")
        chunks = [chunk async for chunk in stream_result]  # type: ignore[union-attr]
        assert chunks == [b"data: {}\n\n"]

    asyncio.run(_run())


def test_llm_proxy_aclose_delegates() -> None:
    async def _run() -> None:
        provider = FakeLlm()
        service = LlmProxyService(provider)
        await service.aclose()
        assert provider.closed == 1

    asyncio.run(_run())


def test_llm_proxy_rejects_bad_chat_shape() -> None:
    class BadLlm(FakeLlm):
        async def chat_completions(
            self,
            body: dict[str, Any],
            *,
            stream: bool = False,
        ) -> dict[str, Any] | AsyncIterator[bytes]:
            _ = body, stream
            return ["not", "a", "dict"]  # type: ignore[return-value]

    async def _run() -> None:
        service = LlmProxyService(BadLlm())
        with pytest.raises(LlmProviderError, match="JSON object"):
            await service.chat_completions({}, stream=False)

    asyncio.run(_run())


def test_tts_synthesize_uses_default_voice() -> None:
    async def _run() -> None:
        engine = FakeTts()
        service = TtsService(engine, default_voice="ko-default")
        await service.synthesize("안녕")
        assert engine.last_voice == "ko-default"

    asyncio.run(_run())


def test_tts_empty_audio_raises() -> None:
    async def _run() -> None:
        service = TtsService(FakeTts(audio=b""), default_voice="ko-default")
        with pytest.raises(TtsError, match="empty audio"):
            await service.synthesize("안녕")

    asyncio.run(_run())


def test_tts_synthesize_request_missing_text() -> None:
    async def _run() -> None:
        service = TtsService(FakeTts(), default_voice="ko-default")
        with pytest.raises(ValueError, match="Missing input text"):
            await service.synthesize_request(SpeechRequest(input="  "))

    asyncio.run(_run())
