# SPDX-License-Identifier: BSD-3-Clause
"""Ollama LLM adapter (mocked httpx)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

pytest.importorskip("httpx")

import httpx

from soju.backend.abstract.llm import LlmProviderError
from soju.backend.adapters.llm import build_llm_provider
from soju.backend.adapters.llm.ollama import OllamaLlmProvider
from soju.backend.config import LlmSettings


class FakeTransport(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Any]] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        import json

        payload = json.loads(request.content.decode()) if request.content else None
        self.calls.append((request.method, request.url.path, payload))
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"object": "list", "data": [{"id": "gemma4:e4b"}]})
        if request.url.path == "/v1/chat/completions":
            if payload and payload.get("stream"):
                return httpx.Response(
                    200,
                    content=b'data: {"ok":true}\n\ndata: [DONE]\n\n',
                    headers={"content-type": "text/event-stream"},
                )
            return httpx.Response(200, json={"choices": [{"message": {"content": "hi"}}]})
        if request.url.path == "/v1/embeddings":
            return httpx.Response(404, json={"error": "missing"})
        if request.url.path == "/api/embeddings":
            return httpx.Response(200, json={"embedding": [0.1, 0.2]})
        return httpx.Response(500, json={"error": "unexpected"})


def test_ollama_provider_models_chat_embed_stream() -> None:
    transport = FakeTransport()

    async def _run() -> None:
        client = httpx.AsyncClient(base_url="http://ollama.test", transport=transport)
        provider = OllamaLlmProvider(
            base_url="http://ollama.test",
            chat_model="gemma4:e4b",
            embed_model="nomic-embed-text",
            client=client,
        )
        try:
            models = await provider.list_models()
            assert models["data"][0]["id"] == "gemma4:e4b"

            chat = await provider.chat_completions({"messages": [{"role": "user", "content": "x"}]}, stream=False)
            assert chat["choices"][0]["message"]["content"] == "hi"
            assert transport.calls[-1][2]["model"] == "gemma4:e4b"

            stream = await provider.chat_completions({"messages": []}, stream=True)
            chunks = b"".join([c async for c in stream])
            assert b"[DONE]" in chunks

            emb = await provider.embeddings({"input": "theme"})
            assert emb["data"][0]["embedding"] == [0.1, 0.2]
            assert emb["model"] == "nomic-embed-text"
        finally:
            await provider.aclose()

    asyncio.run(_run())


def test_build_llm_provider() -> None:
    provider = build_llm_provider(LlmSettings())
    assert provider.name == "ollama"
    asyncio.run(provider.aclose())


def test_ollama_list_models_error() -> None:
    class Boom(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("down", request=request)

    async def _run() -> None:
        client = httpx.AsyncClient(base_url="http://ollama.test", transport=Boom())
        provider = OllamaLlmProvider(
            base_url="http://ollama.test",
            chat_model="m",
            embed_model="e",
            client=client,
        )
        try:
            with pytest.raises(LlmProviderError, match="/v1/models"):
                await provider.list_models()
        finally:
            await provider.aclose()

    asyncio.run(_run())
